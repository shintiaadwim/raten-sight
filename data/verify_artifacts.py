r"""
Skrip Verifikasi Muat Ulang Artefak pada Proses Python Baru (Role Data).

Cara menjalankan:
    .\.venv\Scripts\python.exe data/verify_artifacts.py
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from run_pipeline import evaluate_retention_rule

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT_DIR / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"
ARTIFACTS_DIR = OUTPUT_DIR / "artifacts"


def main():
    print("=== VERIFIKASI MUAT ULANG ARTEFAK PADA PROSES PYTHON BARU ===")
    with open(ARTIFACTS_DIR / "model_metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
    with open(OUTPUT_DIR / "sample_predictions.json", "r", encoding="utf-8") as f:
        expected_samples = json.load(f)

    clf_pipe = joblib.load(ARTIFACTS_DIR / metadata["artifacts"]["classification"])
    cluster_pipe = joblib.load(ARTIFACTS_DIR / metadata["artifacts"]["clustering"])
    reg_pipe = joblib.load(ARTIFACTS_DIR / metadata["artifacts"]["regression"])

    df = pd.read_csv(RAW_CSV)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0.0)
    sample_df = df.iloc[: len(expected_samples)].copy()

    clf_features = metadata["models"]["classification"]["required_features"]
    cluster_features = metadata["models"]["clustering"]["required_features"]
    reg_features = metadata["models"]["regression"]["required_features"]
    threshold = float(metadata["models"]["classification"]["threshold"])
    segment_map = metadata["models"]["clustering"]["segment_id_to_name"]

    probs = clf_pipe.predict_proba(sample_df[clf_features])[:, 1]
    preds = np.where(probs >= threshold, "Yes", "No")
    segs = cluster_pipe.predict(sample_df[cluster_features])
    mc_preds = reg_pipe.predict(sample_df[reg_features])

    mismatches = 0
    for i, exp in enumerate(expected_samples):
        cid = str(sample_df.iloc[i]["customerID"])
        prob_v = round(float(probs[i]), 4)
        pred_lbl = str(preds[i])
        seg_id = int(segs[i])
        seg_name = segment_map.get(str(seg_id), "Unassigned / Perlu Tinjauan Manual")
        mc_pred = round(float(mc_preds[i]), 2)
        rec = evaluate_retention_rule(prob_v, pred_lbl, seg_id)

        assert cid == exp["customer_id"], f"Mismatch customerID: {cid} != {exp['customer_id']}"
        assert np.isclose(prob_v, exp["churn_probability"], atol=1e-4), f"Mismatch prob on {cid}"
        assert pred_lbl == exp["churn_prediction"], f"Mismatch label on {cid}"
        assert seg_id == exp["segment_id"], f"Mismatch segment_id on {cid}"
        assert seg_name == exp["segment_name"], f"Mismatch segment_name on {cid}"
        assert np.isclose(mc_pred, exp["predicted_monthly_charges"], atol=1e-2), f"Mismatch reg on {cid}"
        assert rec == exp["recommendation"], f"Mismatch recommendation on {cid}"

    print(f"Berhasil memverifikasi {len(expected_samples)} baris contoh pada proses Python baru (0 mismatch)!")
    print("Contoh kecocokan baris pertama (customerID = 7590-VHVEG):")
    print(json.dumps(expected_samples[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
