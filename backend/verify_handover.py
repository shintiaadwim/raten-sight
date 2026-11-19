"""Verify installed pipelines against Data's samples and measure local batch work."""

import argparse
import json
from dataclasses import replace
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from backend.batch import BatchProcessor, BatchSettings
from backend.errors import ProcessingError


def compare_predictions(predictions: list[dict], samples: list[dict]) -> None:
    by_id = {row["customer_id"]: row for row in predictions}
    if not samples:
        raise ProcessingError("NO_SAMPLES", "Contoh serah terima Data belum tersedia.")
    for sample in samples:
        customer_id = sample["customer_id"]
        actual = by_id.get(customer_id)
        if actual is None:
            raise ProcessingError("SAMPLE_MISMATCH", f"Pelanggan {customer_id} tidak ditemukan pada hasil Backend.")
        for field in ("churn_prediction", "segment_id", "segment_name", "recommendation"):
            if actual[field] != sample[field]:
                raise ProcessingError("SAMPLE_MISMATCH", f"Hasil {field} berbeda untuk pelanggan {customer_id}.")
        for field, tolerance in (("churn_probability", 0.0001), ("predicted_monthly_charges", 0.01)):
            if not isclose(actual[field], sample[field], abs_tol=tolerance, rel_tol=0):
                raise ProcessingError("SAMPLE_MISMATCH", f"Hasil {field} berbeda untuk pelanggan {customer_id}.")


def verify(settings: BatchSettings, samples: list[dict]) -> dict:
    with TemporaryDirectory(prefix="retensight-handover-") as temporary:
        isolated = replace(settings, results_dir=Path(temporary))
        worker = BatchProcessor(isolated)
        start = perf_counter()
        worker.refresh()
        cold_seconds = perf_counter() - start
        if worker.state.status != "ready":
            raise ProcessingError("HANDOVER_FAILED", json.dumps(worker.state.error, ensure_ascii=False))
        predictions = worker.state.result["predictions"]["predictions"]
        compare_predictions(predictions, samples)

        start = perf_counter()
        restarted = BatchProcessor(isolated)
        restarted.refresh()
        cached_seconds = perf_counter() - start
        if restarted.state != worker.state:
            raise ProcessingError("CACHE_MISMATCH", "Hasil yang dibaca ulang berbeda dari batch awal.")
        if worker.state.result["evaluations"] is None:
            raise ProcessingError("EVALUATIONS_NOT_AVAILABLE", "Paket serah terima belum menyertakan evaluasi.")
        return {
            "dataset_version": worker.state.dataset_version,
            "model_version": worker.state.model_version,
            "processed_rows": len(predictions),
            "matched_samples": len(samples),
            "batch_seconds": round(cold_seconds, 4),
            "cached_reload_seconds": round(cached_seconds, 4),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Cocokkan hasil Backend dengan contoh keluaran Data.")
    parser.add_argument("--samples", type=Path, help="File sample_predictions.json dari tim Data.")
    args = parser.parse_args()
    settings = BatchSettings.from_environment()
    try:
        if args.samples:
            samples = json.loads(args.samples.read_text(encoding="utf-8"))
        else:
            metadata = json.loads(settings.manifest.read_text(encoding="utf-8"))
            sample = metadata.get("sample_expected_output")
            samples = [sample] if sample else []
        report = verify(settings, samples)
    except (ProcessingError, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Verifikasi gagal: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
