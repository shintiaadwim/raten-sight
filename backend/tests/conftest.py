import json
from importlib.metadata import version
from io import BytesIO

import joblib
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from backend.batch import BatchSettings
from backend.model_bundle import REQUIRED_PACKAGES


@pytest.fixture
def sample_csv():
    return (
        "customerID,tenure,Contract,MonthlyCharges,TotalCharges,Churn\n"
        "00123,12,Month-to-month,49.90,598.80,Yes\n"
        '00456,0,One year,19.85," ",No\n'
    ).encode()


@pytest.fixture
def manifest_data():
    return {
        "model_version": "test-v1",
        "dependencies": {package: version(package) for package in sorted(REQUIRED_PACKAGES)},
        "allow_missing_total_charges": True,
        "categories": {"Contract": ["Month-to-month", "One year", "Two year"]},
        "classification": {
            "artifact": "churn.joblib", "algorithm": "Decision Tree", "features": ["tenure", "Contract"],
            "positive_class": 0, "threshold": 0.5,
        },
        "clustering": {
            "artifact": "segments.joblib", "algorithm": "Synthetic segment predictor",
            "features": ["tenure", "MonthlyCharges", "TotalCharges"],
            "segments": [
                {"segment_id": 1, "segment_name": "Langganan lebih lama", "profile": "Tenure lebih panjang."},
                {"segment_id": -1, "segment_name": "Di luar segmen"},
            ],
            "noise_label": -1,
        },
        "regression": {
            "artifact": "charges.joblib", "algorithm": "Decision Tree", "features": ["tenure", "Contract"],
            "unit": "satuan biaya dataset",
        },
        "retention_rules": [
            {"churn_prediction": "Yes", "min_probability": 0.6, "segment_ids": [1], "recommendation": "Tinjau kontrak."},
            {"churn_prediction": "Yes", "recommendation": "Hubungi pelanggan."},
        ],
        "fallback_recommendation": "Pantau pengalaman pelanggan.",
    }


@pytest.fixture(scope="session")
def pipeline_bytes():
    customers = pd.DataFrame({"tenure": [12, 0], "Contract": ["Month-to-month", "One year"]})
    charges = pd.DataFrame({"tenure": [12, 0], "MonthlyCharges": [49.90, 19.85], "TotalCharges": [598.80, float("nan")]})

    def encode_contract():
        return ColumnTransformer(
            [("contract", OneHotEncoder(handle_unknown="ignore"), ["Contract"])], remainder="passthrough",
        )

    pipelines = {
        "classification": make_pipeline(encode_contract(), DecisionTreeClassifier(random_state=0)).fit(customers, [0, 1]),
        "clustering": make_pipeline(SimpleImputer(), DecisionTreeClassifier(random_state=0)).fit(charges, [1, -1]),
        "regression": make_pipeline(encode_contract(), DecisionTreeRegressor(random_state=0)).fit(customers, [51.75, 20.0]),
    }
    serialized = {}
    for name, pipeline in pipelines.items():
        buffer = BytesIO()
        joblib.dump(pipeline, buffer)
        serialized[name] = buffer.getvalue()
    return serialized


@pytest.fixture
def manifest_path(tmp_path, manifest_data, pipeline_bytes):
    path = tmp_path / "artifacts" / "manifest.json"
    path.parent.mkdir()
    path.write_text(json.dumps(manifest_data), encoding="utf-8")
    for kind, content in pipeline_bytes.items():
        path.with_name(manifest_data[kind]["artifact"]).write_bytes(content)
    return path


@pytest.fixture
def batch_settings(tmp_path, sample_csv, manifest_path):
    dataset = tmp_path / "churn.csv"
    dataset.write_bytes(sample_csv)
    return BatchSettings(dataset, manifest_path, tmp_path / "results", poll_seconds=0.02)
