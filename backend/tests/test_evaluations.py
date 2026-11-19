import asyncio
import json

import httpx
import pytest

from backend.batch import BatchProcessor
from backend.dataset import dataset_version
from backend.errors import ProcessingError
from backend.evaluations import read_evaluations
from backend.main import create_app
from backend.model_bundle import read_manifest


def install_evaluations(settings, manifest_data, payload):
    manifest_data["evaluations"] = "evaluations_payload.json"
    manifest_data["source_dataset_version"] = "telco-test-v1"
    settings.manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    path = settings.manifest.with_name(manifest_data["evaluations"])
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_evaluations_share_the_batch_versions_and_invalidate_cache(batch_settings, manifest_data, evaluation_payload):
    path = install_evaluations(batch_settings, manifest_data, evaluation_payload)
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    ready = worker.state
    assert ready.status == "ready"
    assert ready.response("evaluations")["data"] == evaluation_payload
    assert ready.response("evaluations")["model_version"] == ready.response("predictions")["model_version"]

    evaluation_payload["classification"]["test_evaluation"]["f1"] = 0.8
    path.write_text(json.dumps(evaluation_payload), encoding="utf-8")
    worker.refresh()
    assert worker.state.status == "ready"
    assert worker.state.model_version != ready.model_version
    assert worker.state.response("evaluations")["data"] == evaluation_payload

    evaluation_payload["model_version"] = "another-release"
    path.write_text(json.dumps(evaluation_payload), encoding="utf-8")
    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.response("evaluations")["error"]["code"] == "INVALID_EVALUATIONS"
    assert worker.state.response("predictions")["data"] is None


def test_missing_evaluations_does_not_silently_return_other_results(batch_settings, manifest_data, evaluation_payload):
    path = install_evaluations(batch_settings, manifest_data, evaluation_payload)
    path.unlink()
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    assert worker.state.status == "failed"
    assert worker.state.error["code"] == "ARTIFACT_NOT_FOUND"
    path.write_text(json.dumps(evaluation_payload), encoding="utf-8")
    worker.refresh()
    assert worker.state.status == "ready"


def test_legacy_bundle_without_evaluations_has_explicit_api_status(batch_settings):
    app = create_app(batch_settings)

    async def scenario():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                async with asyncio.timeout(8):
                    while (await client.get("/api/dataset-summary")).json()["status"] != "ready":
                        await asyncio.sleep(0.02)
                response = await client.get("/api/evaluations")
                assert response.status_code == 200
                assert response.json()["error"]["code"] == "EVALUATIONS_NOT_AVAILABLE"
                assert response.json()["data"] is None
                assert (await client.get("/api/predictions")).json()["status"] == "ready"

    asyncio.run(scenario())


@pytest.mark.parametrize("payload", [
    '{"bad":',
    '{"model_version": NaN}',
    '{"model_version": 1e9999}',
])
def test_malformed_evaluations_have_actionable_errors(manifest_path, payload):
    _, manifest = read_manifest(manifest_path)
    with pytest.raises(ProcessingError) as error:
        read_evaluations(payload.encode(), manifest)
    assert error.value.code == "INVALID_EVALUATIONS"


def test_declared_source_hash_matches_the_installed_dataset(batch_settings, manifest_data, sample_csv):
    manifest_data["source_dataset_sha256"] = dataset_version(sample_csv).split(":")[1]
    batch_settings.manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    worker = BatchProcessor(batch_settings)
    worker.refresh()
    assert worker.state.status == "ready"
    batch_settings.dataset.write_bytes(sample_csv.replace(b"49.90", b"50.90"))
    worker.refresh()
    assert worker.state.error["code"] == "DATASET_MISMATCH"
