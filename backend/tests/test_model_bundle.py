import json

import pytest

from backend.errors import ProcessingError
from backend.model_bundle import artifact_paths, bundle_version, check_dependencies, load_pipelines, read_manifest


def test_loads_serialized_pipelines_and_finds_the_positive_column(manifest_path):
    raw, manifest = read_manifest(manifest_path)
    files = {name: path.read_bytes() for name, path in artifact_paths(manifest_path, manifest).items()}
    check_dependencies(manifest)
    pipelines = load_pipelines(manifest, files)
    assert list(pipelines.classification.classes_) == [0, 1]
    assert pipelines.positive_index == 0
    version = bundle_version(manifest, raw, files)
    assert version.startswith("test-v1@sha256:")
    assert version != bundle_version(manifest, raw, {**files, "regression": b"changed"})


def test_incompatible_dependency_is_reported(manifest_path, manifest_data):
    manifest_data["dependencies"]["pandas"] = "0.0.0"
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    _, manifest = read_manifest(manifest_path)
    with pytest.raises(ProcessingError, match="Model membutuhkan pandas 0.0.0") as error:
        check_dependencies(manifest)
    assert error.value.code == "DEPENDENCY_MISMATCH"


@pytest.mark.parametrize(("section", "field", "value"), [
    ("regression", "features", ["MonthlyCharges"]),
    ("classification", "features", ["customerID"]),
    ("clustering", "artifact", "../outside.joblib"),
    ("clustering", "noise_label", 999),
    ("classification", "threshold", 1.5),
])
def test_invalid_model_contract_is_reported(manifest_path, manifest_data, section, field, value):
    manifest_data[section][field] = value
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(ProcessingError) as error:
        read_manifest(manifest_path)
    assert error.value.code == "INVALID_MANIFEST"


def test_incorrect_order_of_features_is_rejected(manifest_path, manifest_data, pipeline_bytes):
    manifest_data["classification"]["features"].reverse()
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    _, manifest = read_manifest(manifest_path)
    with pytest.raises(ProcessingError) as error:
        load_pipelines(manifest, pipeline_bytes)
    assert error.value.code == "FEATURE_MISMATCH"


def test_corrupt_pipeline_is_reported(manifest_path, pipeline_bytes):
    _, manifest = read_manifest(manifest_path)
    with pytest.raises(ProcessingError, match="charges.joblib") as error:
        load_pipelines(manifest, {**pipeline_bytes, "regression": b"invalid"})
    assert error.value.code == "INVALID_ARTIFACT"
