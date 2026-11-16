from bisect import bisect_right
from collections import Counter
from collections.abc import Callable, Iterable

import numpy as np
import pandas as pd

from backend.dataset import CustomerRow
from backend.errors import ProcessingError
from backend.model_bundle import LoadedPipelines, ModelManifest


def analyze(rows: list[CustomerRow], manifest: ModelManifest, models: LoadedPipelines) -> dict[str, dict]:
    frame = pd.DataFrame.from_records(rows)
    if "TotalCharges" in frame:
        frame["TotalCharges"] = frame["TotalCharges"].astype(float)

    probabilities = predict(models.classification.predict_proba, frame, manifest.classification.features, "churn")
    if probabilities.shape != (len(rows), 2) or not finite_numeric(probabilities):
        raise ProcessingError("INVALID_MODEL_OUTPUT", "Probabilitas model churn harus berisi dua angka per pelanggan.")
    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ProcessingError("INVALID_MODEL_OUTPUT", "Probabilitas model churn harus berada di antara 0 dan 1.")

    segment_ids = predict(models.clustering.predict, frame, manifest.clustering.features, "segmentasi")
    if segment_ids.shape != (len(rows),) or segment_ids.dtype.kind not in "iu":
        raise ProcessingError("INVALID_MODEL_OUTPUT", "Model segmentasi harus menghasilkan satu ID integer per pelanggan.")

    charges = predict(models.regression.predict, frame, manifest.regression.features, "regresi")
    if charges.shape == (len(rows), 1):
        charges = charges[:, 0]
    if charges.shape != (len(rows),) or not finite_numeric(charges):
        raise ProcessingError("INVALID_MODEL_OUTPUT", "Model regresi harus menghasilkan satu angka per pelanggan.")

    segments = {segment.segment_id: segment for segment in manifest.clustering.segments}
    counts = Counter()
    tenure_totals = Counter()
    predictions = []
    for customer, probability, segment_id, charge in zip(
        rows, probabilities[:, models.positive_index], segment_ids, charges, strict=True,
    ):
        probability = float(probability)
        segment_id = int(segment_id)
        if segment_id not in segments:
            raise ProcessingError("UNKNOWN_SEGMENT", f"ID segmen {segment_id} tidak terdaftar dalam manifest.")
        label = "Yes" if probability >= manifest.classification.threshold else "No"
        counts[segment_id] += 1
        tenure_totals[segment_id] += customer["tenure"]
        predictions.append({
            "customer_id": customer["customerID"],
            "churn_probability": probability,
            "churn_prediction": label,
            "segment_id": segment_id,
            "segment_name": segments[segment_id].segment_name,
            "predicted_monthly_charges": float(charge),
            "recommendation": recommendation(manifest, probability, label, segment_id),
        })

    profiles = [
        {
            **segment.model_dump(),
            "customer_count": counts[segment_id],
            "average_tenure_months": tenure_totals[segment_id] / counts[segment_id] if counts[segment_id] else None,
            "is_noise": segment_id == manifest.clustering.noise_label,
        }
        for segment_id, segment in segments.items()
    ]
    missing_charges = sum("TotalCharges" in row and row["TotalCharges"] is None for row in rows)
    return {
        "dataset_summary": summarize(rows),
        "predictions": {
            "processed_rows": len(rows),
            "warnings": [f"{missing_charges} nilai TotalCharges kosong diteruskan ke pipeline."] if missing_charges else [],
            "predictions": predictions,
        },
        "model_info": {
            "classification": manifest.classification.model_dump(exclude={"artifact"}),
            "clustering": {**manifest.clustering.model_dump(exclude={"artifact", "segments"}), "segments": profiles},
            "regression": manifest.regression.model_dump(exclude={"artifact"}),
        },
    }


def predict(method: Callable, frame: pd.DataFrame, features: list[str], name: str) -> np.ndarray:
    try:
        return np.asarray(method(frame.loc[:, features]))
    except Exception as error:
        raise ProcessingError("INFERENCE_FAILED", f"Model {name} gagal memproses fitur dari dataset.") from error


def finite_numeric(values: np.ndarray) -> bool:
    return values.dtype.kind in "iuf" and bool(np.isfinite(values).all())


def recommendation(manifest: ModelManifest, probability: float, label: str, segment_id: int) -> str:
    for rule in manifest.retention_rules:
        if rule.churn_prediction is not None and rule.churn_prediction != label:
            continue
        if rule.min_probability is not None and probability < rule.min_probability:
            continue
        if rule.max_probability is not None and probability > rule.max_probability:
            continue
        if rule.segment_ids is not None and segment_id not in rule.segment_ids:
            continue
        return rule.recommendation
    return manifest.fallback_recommendation


def summarize(rows: list[CustomerRow]) -> dict:
    churn = Counter(row.get("Churn") for row in rows)
    labeled = churn["Yes"] + churn["No"]
    contracts = Counter(row["Contract"] for row in rows)
    return {
        "processed_rows": len(rows),
        "actual_churn": {
            "yes_count": churn["Yes"], "no_count": churn["No"], "rate": churn["Yes"] / labeled,
        } if labeled else None,
        "distributions": {
            "contract": [{"label": label, "count": count} for label, count in sorted(contracts.items())],
            "tenure": histogram(
                (row["tenure"] for row in rows), (13, 25, 49),
                ("0–12 bulan", "13–24 bulan", "25–48 bulan", "49+ bulan"),
            ),
            "monthly_charges": histogram(
                (row["MonthlyCharges"] for row in rows), (30, 60, 90),
                ("0–<30", "30–<60", "60–<90", "90+"),
            ),
        },
    }


def histogram(values: Iterable, cutoffs: tuple[int, ...], labels: tuple[str, ...]) -> list[dict]:
    counts = Counter(bisect_right(cutoffs, value) for value in values)
    return [{"label": label, "count": counts[index]} for index, label in enumerate(labels)]
