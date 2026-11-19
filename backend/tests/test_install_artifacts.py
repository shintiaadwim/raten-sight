import json

import pytest

from backend.errors import ProcessingError
from backend.install_artifacts import install
from backend.model_bundle import artifact_paths, read_manifest


def prepare_export(manifest_path, manifest_data, evaluation_payload):
    manifest_data["evaluations"] = "evaluations_payload.json"
    manifest_data["source_dataset_version"] = "telco-test-v1"
    manifest_path.with_name("model_metadata.json").write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest_path.parent.parent.joinpath("evaluations_payload.json").write_text(
        json.dumps(evaluation_payload), encoding="utf-8",
    )


def test_installs_outputs_with_hashed_files_and_preserves_evaluations(
    tmp_path, manifest_path, manifest_data, pipeline_bytes, evaluation_payload,
):
    prepare_export(manifest_path, manifest_data, evaluation_payload)
    destination = tmp_path / "backend-models"
    installed = install(manifest_path.parent.parent, destination)
    _, manifest = read_manifest(installed)
    for kind, path in artifact_paths(installed, manifest).items():
        assert path.read_bytes() == pipeline_bytes[kind]
        assert path.name != manifest_data[kind]["artifact"]
    assert json.loads(installed.with_name(manifest.evaluations).read_text()) == evaluation_payload
    assert install(destination, destination) == installed


def test_invalid_evaluations_cannot_replace_active_metadata(
    tmp_path, manifest_path, manifest_data, evaluation_payload,
):
    prepare_export(manifest_path, manifest_data, evaluation_payload)
    destination = tmp_path / "backend-models"
    installed = install(manifest_path.parent.parent, destination)
    previous = installed.read_bytes()
    evaluation_path = manifest_path.parent.parent / "evaluations_payload.json"
    evaluation_path.write_text('{"model_version":"incorrect"}', encoding="utf-8")
    with pytest.raises(ProcessingError) as error:
        install(manifest_path.parent.parent, destination)
    assert error.value.code == "INVALID_EVALUATIONS"
    assert installed.read_bytes() == previous
