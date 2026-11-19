import pytest

from backend.errors import ProcessingError
from backend.verify_handover import compare_predictions


def test_sample_comparison_respects_rounding():
    actual = [{
        "customer_id": "00123", "churn_prediction": "Yes", "segment_id": 0,
        "segment_name": "Baru", "recommendation": "Simulasi", "churn_probability": 0.7053421,
        "predicted_monthly_charges": 29.956,
    }]
    sample = {**actual[0], "churn_probability": 0.7053, "predicted_monthly_charges": 29.96}
    compare_predictions(actual, [sample])
    sample["segment_id"] = 1
    with pytest.raises(ProcessingError) as error:
        compare_predictions(actual, [sample])
    assert error.value.code == "SAMPLE_MISMATCH"
