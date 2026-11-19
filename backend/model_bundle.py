from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
import json
from pathlib import Path
import platform
from typing import Annotated, Any, Literal, Self

import joblib
from pydantic import (
    BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, StringConstraints,
    ValidationError, model_validator,
)

from backend.dataset import AMOUNT_FIELDS, CATEGORICAL_FIELDS, FEATURE_FIELDS
from backend.errors import ProcessingError, read_input
from backend.handover import runtime_manifest

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ArtifactName = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_.-]+\.(joblib|pkl)$")]
EvaluationName = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_.-]+\.json$")]
Probability = Annotated[float, Field(ge=0, le=1)]
REQUIRED_PACKAGES = frozenset({"joblib", "numpy", "pandas", "scikit-learn"})


class Spec(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PipelineSpec(Spec):
    artifact: ArtifactName
    algorithm: Text
    features: list[Text] = Field(min_length=1)


class ClassifierSpec(PipelineSpec):
    positive_class: StrictStr | StrictInt | StrictBool
    threshold: Probability


class Segment(Spec):
    segment_id: StrictInt
    segment_name: Text
    profile: Text | None = None


class ClusterSpec(PipelineSpec):
    segments: list[Segment] = Field(min_length=1)
    noise_label: StrictInt | None = None


class RegressorSpec(PipelineSpec):
    target: Literal["MonthlyCharges"] = "MonthlyCharges"
    unit: Text


class RetentionRule(Spec):
    churn_prediction: Literal["Yes", "No"] | None = None
    min_probability: Probability | None = None
    max_probability: Probability | None = None
    segment_ids: list[StrictInt] | None = Field(default=None, min_length=1)
    recommendation: Text

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.min_probability is not None and self.max_probability is not None:
            if self.min_probability > self.max_probability:
                raise ValueError("min_probability tidak boleh melebihi max_probability.")
        return self


class ModelManifest(Spec):
    model_version: Text
    dependencies: dict[Text, Text]
    allow_missing_total_charges: StrictBool = False
    categories: dict[Text, list[Text]] = Field(default_factory=dict)
    classification: ClassifierSpec
    clustering: ClusterSpec
    regression: RegressorSpec
    retention_rules: list[RetentionRule] = Field(default_factory=list)
    fallback_recommendation: Text
    source_dataset_version: Text | None = None
    source_dataset_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")] | None = None
    evaluations: EvaluationName | None = None

    @property
    def pipelines(self) -> dict[str, PipelineSpec]:
        return {
            "classification": self.classification,
            "clustering": self.clustering,
            "regression": self.regression,
        }

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        missing_packages = REQUIRED_PACKAGES - self.dependencies.keys()
        if missing_packages:
            raise ValueError("Versi dependensi belum tersedia: " + ", ".join(sorted(missing_packages)))
        for kind, spec in self.pipelines.items():
            unknown = set(spec.features) - FEATURE_FIELDS
            if unknown:
                raise ValueError(f"Fitur {kind} tidak didukung: " + ", ".join(sorted(unknown)))
            if len(spec.features) != len(set(spec.features)):
                raise ValueError(f"Daftar fitur {kind} berisi duplikat.")
        if AMOUNT_FIELDS.intersection(self.regression.features):
            raise ValueError("Fitur regresi mengandung MonthlyCharges atau TotalCharges.")
        if self.categories.keys() - CATEGORICAL_FIELDS or any(not values for values in self.categories.values()):
            raise ValueError("categories harus memetakan kolom kategorikal ke daftar nilai yang terisi.")
        segment_ids = {segment.segment_id for segment in self.clustering.segments}
        if len(segment_ids) != len(self.clustering.segments):
            raise ValueError("ID segmen duplikat.")
        if self.clustering.noise_label is not None and self.clustering.noise_label not in segment_ids:
            raise ValueError("noise_label harus terdaftar dalam segments.")
        if any(set(rule.segment_ids or ()) - segment_ids for rule in self.retention_rules):
            raise ValueError("retention_rules merujuk pada ID segmen yang belum terdaftar.")
        return self


@dataclass(frozen=True)
class LoadedPipelines:
    classification: Any
    clustering: Any
    regression: Any
    positive_index: int


def read_manifest(path: Path) -> tuple[bytes, ModelManifest]:
    raw = read_input(path, "MANIFEST", "Manifest model")
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "models" in data:
            data = runtime_manifest(data)
        return raw, ModelManifest.model_validate(data)
    except ValidationError as error:
        detail = error.errors(include_url=False, include_input=False, include_context=False)[0]
        location = ".".join(map(str, detail["loc"]))
        message = f"{location}: {detail['msg']}" if location else detail["msg"]
        raise ProcessingError("INVALID_MANIFEST", f"Manifest model tidak valid. {message}") from error
    except (ValueError, KeyError, TypeError, SyntaxError) as error:
        raise ProcessingError("INVALID_MANIFEST", f"Metadata model tidak valid. {error}") from error


def check_dependencies(manifest: ModelManifest) -> None:
    for package, expected in manifest.dependencies.items():
        if package == "python":
            installed_python = platform.python_version()
            if installed_python.split(".")[:2] != expected.split(".")[:2]:
                raise ProcessingError(
                    "DEPENDENCY_MISMATCH", f"Model memakai Python {expected}, versi terpasang {installed_python}.",
                )
            continue
        try:
            installed = version(package)
        except PackageNotFoundError as error:
            raise ProcessingError("DEPENDENCY_MISMATCH", f"Dependensi model {package} belum terpasang.") from error
        if installed != expected:
            raise ProcessingError(
                "DEPENDENCY_MISMATCH",
                f"Model membutuhkan {package} {expected}, versi terpasang {installed}.",
            )


def artifact_paths(path: Path, manifest: ModelManifest) -> dict[str, Path]:
    return {kind: path.with_name(spec.artifact) for kind, spec in manifest.pipelines.items()}


def bundle_version(manifest: ModelManifest, raw: bytes, files: dict[str, bytes]) -> str:
    digest = sha256(raw)
    for name in sorted(files):
        digest.update(sha256(files[name]).digest())
    return f"{manifest.model_version}@sha256:{digest.hexdigest()}"


def load_pipelines(manifest: ModelManifest, files: dict[str, bytes]) -> LoadedPipelines:
    pipelines = {}
    for kind, spec in manifest.pipelines.items():
        try:
            pipeline = joblib.load(BytesIO(files[kind]))
        except Exception as error:
            raise ProcessingError("INVALID_ARTIFACT", f"Artefak {spec.artifact} gagal dimuat.") from error
        method = "predict_proba" if kind == "classification" else "predict"
        if not callable(getattr(pipeline, method, None)):
            raise ProcessingError("INVALID_ARTIFACT", f"Artefak {spec.artifact} harus menyediakan {method}().")
        names = getattr(pipeline, "feature_names_in_", None)
        count = getattr(pipeline, "n_features_in_", len(spec.features))
        if (names is not None and list(names) != spec.features) or count != len(spec.features):
            raise ProcessingError("FEATURE_MISMATCH", f"Fitur manifest tidak cocok dengan artefak {spec.artifact}.")
        pipelines[kind] = pipeline

    classes = getattr(pipelines["classification"], "classes_", None)
    if classes is None or len(classes) != 2:
        raise ProcessingError("INVALID_ARTIFACT", "Model churn harus mempunyai dua kelas.")
    matches = [index for index, label in enumerate(classes) if label == manifest.classification.positive_class]
    if len(matches) != 1:
        raise ProcessingError("INVALID_ARTIFACT", "Kelas positif pada manifest tidak cocok dengan kelas model churn.")
    return LoadedPipelines(**pipelines, positive_index=matches[0])
