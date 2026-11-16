import json
import logging
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Event
from typing import Literal

from backend.dataset import dataset_version, read_dataset
from backend.errors import ProcessingError, read_input
from backend.inference import analyze
from backend.model_bundle import artifact_paths, bundle_version, check_dependencies, load_pipelines, read_manifest

logger = logging.getLogger(__name__)
DATASET_NAME = "IBM Telco Customer Churn"
CACHE_FORMAT_VERSION = 1
RESULT_KEYS = ("dataset_summary", "predictions", "model_info")


@dataclass(frozen=True)
class BatchSettings:
    dataset: Path
    manifest: Path
    results_dir: Path
    poll_seconds: float = 2.0

    @classmethod
    def from_environment(cls) -> "BatchSettings":
        backend_dir = Path(__file__).resolve().parent
        dataset = backend_dir.parent / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
        return cls(
            dataset=Path(os.getenv("RETENSIGHT_DATASET_PATH", str(dataset))),
            manifest=Path(os.getenv("RETENSIGHT_MODEL_MANIFEST", str(backend_dir / "artifacts" / "manifest.json"))),
            results_dir=Path(os.getenv("RETENSIGHT_RESULTS_DIR", str(backend_dir / "results"))),
        )


@dataclass(frozen=True)
class BatchState:
    status: Literal["preparing", "ready", "failed"]
    dataset_version: str | None = None
    model_version: str | None = None
    result: dict[str, dict] | None = None
    error: dict | None = None

    def response(self, section: str) -> dict:
        body = {
            "is_demo": False,
            "status": self.status,
            "dataset_version": self.dataset_version,
            "model_version": self.model_version,
            "data": self.result[section] if self.result is not None else None,
            "error": self.error,
        }
        if section == "dataset_summary":
            body["dataset_name"] = DATASET_NAME
        return body


class BatchProcessor:
    def __init__(self, settings: BatchSettings):
        self.settings = settings
        self.state = BatchState("preparing")
        self._inputs = (settings.dataset, settings.manifest)
        self._watched = self._inputs
        self._observed = None

    def watch(self, stop: Event) -> None:
        while not stop.is_set():
            self.refresh()
            stop.wait(self.settings.poll_seconds)

    def refresh(self) -> None:
        observed = tuple(file_stamp(path) for path in self._watched)
        if observed == self._observed:
            return
        self._watched = self._inputs
        self._observed = observed[:len(self._inputs)]
        self.state = BatchState("preparing")
        data_version = None
        model_version = None
        model_release = None

        try:
            content = read_input(self.settings.dataset, "DATASET", "Dataset")
            data_version = dataset_version(content)
            manifest_raw, manifest = read_manifest(self.settings.manifest)
            model_release = manifest.model_version
            paths = artifact_paths(self.settings.manifest, manifest)
            self._watched += tuple(paths.values())
            self._observed += tuple(file_stamp(path) for path in paths.values())
            files = {kind: read_input(path, "ARTIFACT", "Artefak model") for kind, path in paths.items()}
            model_version = bundle_version(manifest, manifest_raw, files)
            self.state = BatchState("preparing", data_version, model_version)
            if not self._inputs_are_current():
                return

            check_dependencies(manifest)
            cache_key = sha256(f"{data_version}\n{model_version}".encode()).hexdigest()
            target = self.settings.results_dir / f"{cache_key}.json"
            result = read_cached_result(target, data_version, model_version)
            if result is None:
                features = {feature for spec in manifest.pipelines.values() for feature in spec.features}
                rows = read_dataset(
                    content, features, allow_missing_total_charges=manifest.allow_missing_total_charges,
                    categories=manifest.categories,
                )
                result = analyze(rows, manifest, load_pipelines(manifest, files))
                if not self._inputs_are_current():
                    return
                save_result(target, data_version, model_version, result)
            if self._inputs_are_current():
                self.state = BatchState("ready", data_version, model_version, result)
        except ProcessingError as error:
            logger.warning("Batch gagal (%s, %s): %s", data_version, model_version or model_release, error)
            if self._inputs_are_current():
                details = error.as_dict()
                if model_version is None and model_release is not None:
                    details["model_release"] = model_release
                self.state = BatchState("failed", data_version, model_version, error=details)
        except Exception:
            logger.exception("Batch gagal (%s, %s)", data_version, model_version)
            if self._inputs_are_current():
                self.state = BatchState(
                    "failed", data_version, model_version,
                    error={"code": "BATCH_FAILED", "message": "Analisis gagal. Periksa log Backend."},
                )

    def _inputs_are_current(self) -> bool:
        return self._observed == tuple(file_stamp(path) for path in self._watched)


def file_stamp(path: Path) -> tuple[int, int, int, int] | int | None:
    try:
        info = path.stat()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error.errno
    return info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def read_cached_result(path: Path, data_version: str, model_version: str) -> dict[str, dict] | None:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None
    except OSError as error:
        raise ProcessingError("RESULTS_READ_ERROR", "Hasil analisis tersimpan gagal dibaca.") from error
    if not isinstance(record, dict) or (
        record.get("format_version"), record.get("dataset_version"), record.get("model_version")
    ) != (CACHE_FORMAT_VERSION, data_version, model_version):
        return None
    result = record.get("result")
    if not isinstance(result, dict) or any(not isinstance(result.get(key), dict) for key in RESULT_KEYS):
        return None
    return result


def save_result(path: Path, data_version: str, model_version: str, result: dict[str, dict]) -> None:
    temp_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as temp:
            temp_path = Path(temp.name)
            json.dump(
                {
                    "format_version": CACHE_FORMAT_VERSION, "dataset_version": data_version,
                    "model_version": model_version, "result": result,
                },
                temp, ensure_ascii=False, allow_nan=False,
            )
        temp_path.replace(path)
    except (OSError, ValueError) as error:
        raise ProcessingError("RESULTS_WRITE_ERROR", "Hasil analisis gagal disimpan.") from error
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
