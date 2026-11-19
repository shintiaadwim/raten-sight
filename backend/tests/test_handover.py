import json
import platform

import pytest

from backend.errors import ProcessingError
from backend.handover import rule_conditions
from backend.inference import recommendation
from backend.model_bundle import check_dependencies, load_pipelines, read_manifest


@pytest.fixture
def native_metadata(manifest_data):
    return {
        "model_version": manifest_data["model_version"],
        "dataset_version": "telco-test-v1",
        "id_column": "customerID",
        "dependencies": {**manifest_data["dependencies"], "python": platform.python_version()},
        "artifacts": {kind: spec["artifact"] for kind, spec in manifest_data.items() if kind in ("classification", "clustering", "regression")},
        "models": {
            "classification": {
                "selected_model": "Decision Tree",
                "required_features": manifest_data["classification"]["features"],
                "positive_class": "Yes", "threshold": 0.55,
            },
            "clustering": {
                "selected_model": "Synthetic segments",
                "required_features": manifest_data["clustering"]["features"],
                "segment_id_to_name": {"1": "Langganan lebih lama", "2": "Baru tagihan tinggi", "0": "Hemat", "3": "Loyal hemat"},
                "noise_handling_policy": {"selected_model_produces_noise": False, "noise_label": -1},
            },
            "regression": {
                "selected_model": "Decision Tree",
                "required_features": manifest_data["regression"]["features"],
                "target_column": "MonthlyCharges", "currency_unit": "USD",
            },
        },
        "retention_simulation_rules": {
            "rules": [
                {"priority": 1, "condition": "churn_probability >= 0.70 AND segment_id IN (1, 2)", "recommendation": "priority 1"},
                {"priority": 2, "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id == 2", "recommendation": "priority 2"},
                {"priority": 3, "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id == 1", "recommendation": "priority 3"},
                {"priority": 4, "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id IN (0, 3)", "recommendation": "priority 4"},
                {"priority": 5, "condition": "churn_prediction == 'No' AND (segment_id == 2 OR churn_probability >= 0.40)", "recommendation": "priority 5"},
                {"priority": 6, "condition": "Default (churn_prediction == 'No' AND churn_probability < 0.40 AND segment_id != 2)", "recommendation": "priority 6"},
            ],
            "missing_input_fallback": "missing",
        },
    }


def test_reads_data_export_and_binds_numeric_positive_class(tmp_path, native_metadata, pipeline_bytes):
    path = tmp_path / "model_metadata.json"
    path.write_text(json.dumps(native_metadata), encoding="utf-8")
    _, manifest = read_manifest(path)
    check_dependencies(manifest)
    models = load_pipelines(manifest, pipeline_bytes)
    assert manifest.classification.positive_class == 1
    assert models.positive_index == 1
    assert manifest.evaluations == "evaluations_payload.json"
    assert manifest.regression.unit == "USD"
    assert manifest.source_dataset_version == "telco-test-v1"
    for probability, label, segment, expected in [
        (0.7, "Yes", 1, "priority 1"), (0.6, "Yes", 2, "priority 2"),
        (0.6, "Yes", 1, "priority 3"), (0.6, "Yes", 3, "priority 4"),
        (0.2, "No", 2, "priority 5"), (0.4, "No", 0, "priority 5"), (0.2, "No", 0, "priority 6"),
    ]:
        assert recommendation(manifest, probability, label, segment) == expected


@pytest.mark.parametrize("expression", [
    "__import__('os').getcwd()",
    "unknown_field == 1",
    "churn_probability > 0.5",
])
def test_rejects_unrecognised_retention_conditions(expression):
    with pytest.raises((ValueError, SyntaxError)):
        rule_conditions(expression)


def test_invalid_native_metadata_produces_operational_error(tmp_path, native_metadata):
    native_metadata["models"]["classification"]["positive_class"] = "No"
    path = tmp_path / "model_metadata.json"
    path.write_text(json.dumps(native_metadata), encoding="utf-8")
    with pytest.raises(ProcessingError) as error:
        read_manifest(path)
    assert error.value.code == "INVALID_MANIFEST"
