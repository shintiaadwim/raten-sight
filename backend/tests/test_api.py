import asyncio
import json
from pathlib import Path
from threading import Event

import httpx

from backend import batch
from backend.dataset import dataset_version
from backend.main import create_app

ENDPOINTS = ("/api/dataset-summary", "/api/predictions", "/api/model-info")


async def fetch_snapshot(client):
    responses = await asyncio.gather(*(client.get(endpoint) for endpoint in ENDPOINTS))
    for response in responses:
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
    return [response.json() for response in responses]


async def wait_for_summary(client, status):
    async with asyncio.timeout(8):
        while True:
            response = await client.get(ENDPOINTS[0])
            if response.json()["status"] == status:
                return response.json()
            await asyncio.sleep(0.02)


def test_api_survives_missing_source_and_becomes_ready(batch_settings, sample_csv):
    batch_settings.dataset.unlink()
    app = create_app(batch_settings)

    async def scenario():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                failed = await wait_for_summary(client, "failed")
                assert failed["error"]["code"] == "DATASET_NOT_FOUND"
                assert failed["data"] is None
                assert (await client.get("/api/health")).json() == {"status": "ok"}

                batch_settings.dataset.write_bytes(sample_csv)
                ready = await wait_for_summary(client, "ready")
                assert ready["dataset_version"] == dataset_version(sample_csv)
                assert ready["data"]["processed_rows"] == 2

    asyncio.run(scenario())


def test_concurrent_reads_see_consistent_versions_and_status(batch_settings, sample_csv, monkeypatch):
    scoring = Event()
    release = Event()
    original_analyze = batch.analyze

    def delayed_analyze(*args):
        scoring.set()
        if not release.wait(10):
            raise RuntimeError("Test did not release the inference worker.")
        return original_analyze(*args)

    monkeypatch.setattr(batch, "analyze", delayed_analyze)
    app = create_app(batch_settings)

    async def scenario():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test",
                headers={"Origin": "http://localhost:3000"},
            ) as client:
                try:
                    assert await asyncio.to_thread(scoring.wait, 8)
                    preparing = await fetch_snapshot(client)
                    assert {entry["status"] for entry in preparing} == {"preparing"}
                    assert len({(entry["dataset_version"], entry["model_version"]) for entry in preparing}) == 1
                    assert all(entry["data"] is None for entry in preparing)
                    assert not batch_settings.results_dir.exists()
                    health = await client.get("/api/health")
                    assert health.json() == {"status": "ok"}
                    assert health.headers["access-control-allow-origin"] == "http://localhost:3000"
                finally:
                    release.set()

                await wait_for_summary(client, "ready")
                summary, predictions, model_info = await fetch_snapshot(client)
                assert {entry["status"] for entry in (summary, predictions, model_info)} == {"ready"}
                assert all(entry["is_demo"] is False for entry in (summary, predictions, model_info))
                assert summary["dataset_version"] == predictions["dataset_version"] == model_info["dataset_version"]
                assert summary["model_version"] == predictions["model_version"] == model_info["model_version"]
                assert [row["customer_id"] for row in predictions["data"]["predictions"]] == ["00123", "00456"]
                assert len(list(batch_settings.results_dir.glob("*.json"))) == 1
                fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "dashboard.demo.json"
                demo = json.loads(fixture_path.read_text(encoding="utf-8"))["ready"]
                responses = {"dataset_summary": summary, "predictions": predictions, "model_info": model_info}
                for name, response in responses.items():
                    assert response.keys() == demo[name].keys()
                    assert response["data"].keys() == demo[name]["data"].keys()

                invalid = sample_csv.replace(b",12,", b",abc,")
                batch_settings.dataset.write_bytes(invalid)
                await wait_for_summary(client, "failed")
                failed = await fetch_snapshot(client)
                assert all(entry["data"] is None for entry in failed)
                assert {entry["dataset_version"] for entry in failed} == {dataset_version(invalid)}
                assert {entry["model_version"] for entry in failed} == {summary["model_version"]}
                assert {entry["error"]["code"] for entry in failed} == {"INVALID_FIELD"}

    asyncio.run(scenario())
