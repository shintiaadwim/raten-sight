from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from backend.dataset import read_dataset
from backend.errors import ProcessingError
from backend.inference import analyze
from backend.model_bundle import load_pipelines, read_manifest


@pytest.fixture
def analysis_inputs(sample_csv, manifest_path, pipeline_bytes):
    _, manifest = read_manifest(manifest_path)
    rows = read_dataset(
        sample_csv, {feature for model in manifest.pipelines.values() for feature in model.features},
        allow_missing_total_charges=manifest.allow_missing_total_charges, categories=manifest.categories,
    )
    return rows, manifest, load_pipelines(manifest, pipeline_bytes)


def test_joins_outputs_and_keeps_actual_churn_separate(analysis_inputs):
    report = analyze(*analysis_inputs)
    predictions = report["predictions"]["predictions"]
    assert [row["customer_id"] for row in predictions] == ["00123", "00456"]
    assert [row["churn_probability"] for row in predictions] == [1.0, 0.0]
    assert [row["churn_prediction"] for row in predictions] == ["Yes", "No"]
    assert [row["predicted_monthly_charges"] for row in predictions] == [51.75, 20.0]
    assert [row["segment_id"] for row in predictions] == [1, -1]
    assert [row["recommendation"] for row in predictions] == ["Tinjau kontrak.", "Pantau pengalaman pelanggan."]
    assert report["predictions"]["warnings"]
    assert report["dataset_summary"]["actual_churn"] == {"yes_count": 1, "no_count": 1, "rate": 0.5}
    assert report["dataset_summary"]["processed_rows"] == report["predictions"]["processed_rows"] == 2
    assert all(
        sum(bucket["count"] for bucket in buckets) == 2
        for buckets in report["dataset_summary"]["distributions"].values()
    )
    profiles = report["model_info"]["clustering"]["segments"]
    assert [(segment["is_noise"], segment["customer_count"]) for segment in profiles] == [(False, 1), (True, 1)]


def test_one_column_regression_and_absent_historical_labels(analysis_inputs):
    rows, manifest, models = analysis_inputs
    for row in rows:
        del row["Churn"]
    models = replace(models, regression=SimpleNamespace(predict=lambda _: np.array([[51.75], [20.0]])))
    report = analyze(rows, manifest, models)
    assert report["dataset_summary"]["actual_churn"] is None
    assert [row["predicted_monthly_charges"] for row in report["predictions"]["predictions"]] == [51.75, 20.0]


@pytest.mark.parametrize(("task", "method", "result", "code"), [
    ("classification", "predict_proba", [[0.8, 0.2]], "INVALID_MODEL_OUTPUT"),
    ("classification", "predict_proba", [[1.5, 0.0], [0.0, 1.0]], "INVALID_MODEL_OUTPUT"),
    ("clustering", "predict", [1, 100], "UNKNOWN_SEGMENT"),
    ("clustering", "predict", [1, 0.9], "INVALID_MODEL_OUTPUT"),
    ("regression", "predict", [20.0, float("nan")], "INVALID_MODEL_OUTPUT"),
])
def test_no_partial_results_when_a_model_output_is_invalid(analysis_inputs, task, method, result, code):
    rows, manifest, models = analysis_inputs
    replacement = SimpleNamespace(**{method: lambda _: result})
    with pytest.raises(ProcessingError) as error:
        analyze(rows, manifest, replace(models, **{task: replacement}))
    assert error.value.code == code
