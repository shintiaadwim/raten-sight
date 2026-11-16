import json
from dataclasses import replace

from backend import batch
from backend.batch import BatchProcessor
from backend.dataset import dataset_version


def replace_file(path, contents):
    temporary = path.with_suffix(".new")
    temporary.write_bytes(contents)
    temporary.replace(path)


def test_batch_waits_for_inputs_then_recovers(batch_settings, sample_csv, pipeline_bytes):
    batch_settings.dataset.unlink()
    charges = batch_settings.manifest.with_name("charges.joblib")
    charges.unlink()
    worker = BatchProcessor(batch_settings)

    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.error["code"] == "DATASET_NOT_FOUND"

    batch_settings.dataset.write_bytes(sample_csv)
    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.dataset_version == dataset_version(sample_csv)
    assert worker.state.error["code"] == "ARTIFACT_NOT_FOUND"
    assert worker.state.error["model_release"] == "test-v1"

    charges.write_bytes(pipeline_bytes["regression"])
    worker.refresh()
    assert worker.state.status == "ready"
    assert worker.state.error is None


def test_batch_reuses_results_and_updates_each_version(batch_settings, sample_csv, manifest_data, monkeypatch):
    original_analyze = batch.analyze
    calls = []

    def analyze_once(*args):
        calls.append(1)
        return original_analyze(*args)

    monkeypatch.setattr(batch, "analyze", analyze_once)
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    active = worker.state
    assert active.status == "ready"
    assert len(calls) == 1

    worker.refresh()
    assert worker.state is active
    restarted = BatchProcessor(batch_settings)
    restarted.refresh()
    assert restarted.state == active
    assert len(calls) == 1

    new_csv = sample_csv.replace(b"49.90", b"50.90")
    replace_file(batch_settings.dataset, new_csv)
    worker.refresh()
    assert worker.state.status == "ready"
    assert worker.state.dataset_version == dataset_version(new_csv)
    assert worker.state.model_version == active.model_version
    assert len(calls) == 2

    manifest_data["model_version"] = "test-v2"
    replace_file(batch_settings.manifest, json.dumps(manifest_data).encode())
    worker.refresh()
    assert worker.state.status == "ready"
    assert worker.state.model_version.startswith("test-v2@sha256:")
    assert worker.state.dataset_version == dataset_version(new_csv)
    assert len(calls) == 3
    assert len(list(batch_settings.results_dir.glob("*.json"))) == 3


def test_artifact_change_cannot_reuse_previous_result(batch_settings, pipeline_bytes):
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    active = worker.state
    charges = batch_settings.manifest.with_name("charges.joblib")
    replace_file(charges, b"corrupt")
    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.model_version != active.model_version
    assert worker.state.error["code"] == "INVALID_ARTIFACT"
    assert worker.state.response("predictions")["data"] is None

    replace_file(charges, pipeline_bytes["regression"])
    worker.refresh()
    assert worker.state == active


def test_failed_dataset_has_context_without_old_predictions(batch_settings, sample_csv):
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    previous_model = worker.state.model_version
    invalid = sample_csv.replace(b",12,", b",abc,")
    replace_file(batch_settings.dataset, invalid)

    worker.refresh()
    response = worker.state.response("dataset_summary")
    assert response["status"] == "failed"
    assert response["dataset_version"] == dataset_version(invalid)
    assert response["model_version"] == previous_model
    assert response["data"] is None
    assert response["error"]["field"] == "tenure"
    assert response["error"]["row"] == 2
    assert worker.state.response("predictions")["data"] is None


def test_version_change_during_processing_has_no_early_publish(batch_settings, sample_csv, monkeypatch):
    original_analyze = batch.analyze
    new_csv = sample_csv.replace(b"49.90", b"51.90")

    def analyze_and_change_input(*args):
        result = original_analyze(*args)
        replace_file(batch_settings.dataset, new_csv)
        return result

    monkeypatch.setattr(batch, "analyze", analyze_and_change_input)
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    assert worker.state.status == "preparing"
    assert worker.state.result is None
    assert not batch_settings.results_dir.exists()

    monkeypatch.setattr(batch, "analyze", original_analyze)
    worker.refresh()
    assert worker.state.status == "ready"
    assert worker.state.dataset_version == dataset_version(new_csv)


def test_failed_save_cannot_publish_ready(batch_settings):
    unavailable = batch_settings.dataset
    worker = BatchProcessor(replace(batch_settings, results_dir=unavailable))
    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.result is None
    assert worker.state.error["code"] in {"RESULTS_READ_ERROR", "RESULTS_WRITE_ERROR"}


def test_rebuilds_incomplete_cached_results(batch_settings):
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    saved = next(batch_settings.results_dir.glob("*.json"))
    saved.write_text('{"result":', encoding="utf-8")

    restarted = BatchProcessor(batch_settings)
    restarted.refresh()
    assert restarted.state == worker.state
    assert json.loads(saved.read_text(encoding="utf-8"))["result"] == worker.state.result
