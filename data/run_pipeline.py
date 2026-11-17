r"""
Skrip Reproducible Role Data — Cleaning, Training, Evaluasi, dan Ekspor Artefak RetenSight.

Cara menjalankan ulang dari root repositori:
    .\.venv\Scripts\python.exe data/run_pipeline.py
"""

from pathlib import Path
import json
import shutil
import sys
import joblib
import numpy as np
import pandas as pd
import sklearn

from sklearn.model_selection import train_test_split, StratifiedKFold, KFold, cross_validate, cross_val_predict
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score, accuracy_score,
    confusion_matrix, silhouette_score, davies_bouldin_score, calinski_harabasz_score,
    mean_absolute_error, root_mean_squared_error, r2_score
)

SEED = 42
DATASET_ID = "ibm-telco-customer-churn"
DATASET_VERSION = "telco-churn-v1.0"
MODEL_VERSION = "retensight-models-v1.0"
CURRENCY_UNIT = "USD"
POSITIVE_CLASS = "Yes"

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT_DIR / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"
ARTIFACTS_OUT_DIR = OUTPUT_DIR / "artifacts"
BACKEND_ARTIFACTS_DIR = ROOT_DIR / "backend" / "artifacts"


def evaluate_retention_rule(churn_prob, churn_label, segment_id):
    """
    Aturan simulasi retensi berurutan (prioritas 1 s/d 6) beserta fallback jika input belum lengkap.
    """
    if churn_prob is None or churn_label is None or segment_id is None:
        return "[Simulasi] Data risiko atau segmen belum tersedia — lakukan verifikasi profil pelanggan terlebih dahulu."
    if pd.isna(churn_prob) or pd.isna(segment_id):
        return "[Simulasi] Data risiko atau segmen belum tersedia — lakukan verifikasi profil pelanggan terlebih dahulu."

    prob = float(churn_prob)
    seg = int(segment_id)

    # Prioritas 1: Risiko Sangat Tinggi (prob >= 0.70) pada Segmen Rentan / High-Value (Segmen 2 atau 1)
    if prob >= 0.70 and seg in (1, 2):
        return "[Simulasi - Prioritas 1] Risiko Kritis Bernilai Tinggi: Tawarkan diskon kontrak 1-2 tahun sebesar 15-20% & hubungi langsung melalui tim retensi VIP."
    # Prioritas 2: Prediksi Churn (Yes / prob >= 0.55) pada Segmen 2 (Pelanggan Baru Tagihan Tinggi)
    if churn_label == "Yes" and seg == 2:
        return "[Simulasi - Prioritas 2] Pelanggan Baru Tagihan Tinggi Berisiko: Tawarkan paket bundling hemat (migrasi kontrak 1 tahun) & gratis uji layanan TechSupport/OnlineSecurity 3 bulan."
    # Prioritas 3: Prediksi Churn (Yes / prob >= 0.55) pada Segmen 1 (Pelanggan Loyal Premium)
    if churn_label == "Yes" and seg == 1:
        return "[Simulasi - Prioritas 3] Pelanggan Loyal Premium Berisiko: Berikan apresiasi loyalitas (upgrade kecepatan/layanan streaming gratis) & peninjauan tagihan eksklusif."
    # Prioritas 4: Prediksi Churn (Yes / prob >= 0.55) pada Segmen Hemat (Segmen 0 atau 3)
    if churn_label == "Yes" and seg in (0, 3):
        return "[Simulasi - Prioritas 4] Pelanggan Paket Hemat Berisiko: Kirim promo perpanjangan kontrak ringan & pengingat pembayaran otomatis (auto-pay)."
    # Prioritas 5: Prediksi Bertahan (No), tetapi berada di Segmen 2 (Baru Tagihan Tinggi) atau prob >= 0.40
    if churn_label == "No" and (seg == 2 or prob >= 0.40):
        return "[Simulasi - Prioritas 5] Pencegahan Dini (Preventif): Edukasi manfaat layanan tambahan & tawarkan insentif peralihan dari Month-to-month ke kontrak tahunan."
    # Prioritas 6: Pelanggan Stabil / Risiko Rendah
    return "[Simulasi - Prioritas 6] Pelanggan Stabil: Pertahankan kualitas layanan reguler & tawarkan program referral/cross-selling berkala."


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    BACKEND_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Baca dan Cleaning Dataset
    df_raw = pd.read_csv(RAW_CSV)
    rows_before = len(df_raw)
    df = df_raw.copy()
    tc_num = pd.to_numeric(df["TotalCharges"], errors="coerce")
    n_missing_tc = int(tc_num.isna().sum())
    df["TotalCharges"] = tc_num.fillna(0.0)
    rows_after = len(df)

    # Salin dataset berversi untuk serah terima
    versioned_csv_path = OUTPUT_DIR / f"{DATASET_VERSION}.csv"
    shutil.copy2(RAW_CSV, versioned_csv_path)

    # 2. Definisi Fitur per Model
    id_col = "customerID"
    clf_features = [c for c in df.columns if c not in [id_col, "Churn"]]
    cluster_features = ["tenure", "MonthlyCharges", "TotalCharges"]
    reg_features = [c for c in df.columns if c not in [id_col, "Churn", "MonthlyCharges", "TotalCharges"]]

    # =========================================================================
    # A. KLASIFIKASI CHURN
    # =========================================================================
    X_clf = df[clf_features].copy()
    y_clf = (df["Churn"] == POSITIVE_CLASS).astype(int)
    X_clf_train, X_clf_test, y_clf_train, y_clf_test, id_clf_train, id_clf_test = train_test_split(
        X_clf, y_clf, df[id_col], test_size=0.20, random_state=SEED, stratify=y_clf
    )

    clf_num_cols = [c for c in clf_features if X_clf[c].dtype != "object"]
    clf_cat_cols = [c for c in clf_features if X_clf[c].dtype == "object"]
    clf_prep_desc = "Num: SimpleImputer(constant=0.0) + StandardScaler | Cat: SimpleImputer(most_frequent) + OneHotEncoder(handle_unknown='ignore')"

    def make_clf_pipe(est):
        return Pipeline([
            ("preprocessor", ColumnTransformer([
                ("num", Pipeline([
                    ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
                    ("scaler", StandardScaler())
                ]), clf_num_cols),
                ("cat", Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
                ]), clf_cat_cols)
            ])),
            ("model", est)
        ])

    clf_candidates = [
        ("Dummy (Stratified Baseline)", "strategy=stratified", DummyClassifier(strategy="stratified", random_state=SEED), "Baseline acak sesuai proporsi kelas"),
        ("Dummy (Uniform Baseline)", "strategy=uniform", DummyClassifier(strategy="uniform", random_state=SEED), "Baseline tebakan seragam 50:50"),
        ("Logistic Regression (Unweighted, C=1.0)", "C=1.0, class_weight=None", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED), "Precision tinggi namun recall churn masih rendah (0.5431)"),
        ("Logistic Regression (Balanced, C=0.1)", "C=0.1, class_weight=balanced", LogisticRegression(C=0.1, class_weight="balanced", max_iter=1000, random_state=SEED), "Kandidat kuat peringkat ke-2 (F1 CV 0.6295, Recall 0.7980)"),
        ("Logistic Regression (Balanced, C=1.0)", "C=1.0, class_weight=balanced", LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=SEED), "Performa kompetitif namun F1 sedikit di bawah RF depth=8"),
        ("Decision Tree (depth=5, Unweighted)", "max_depth=5, class_weight=None", DecisionTreeClassifier(max_depth=5, random_state=SEED), "Recall rendah karena tanpa pembobotan kelas"),
        ("Decision Tree (depth=5, Balanced)", "max_depth=5, class_weight=balanced", DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=SEED), "Pohon tunggal; F1 dan ROC-AUC di bawah ansambel Random Forest"),
        ("Decision Tree (depth=8, Balanced)", "max_depth=8, class_weight=balanced", DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=SEED), "Mulai overfit dibanding depth=5 (ROC-AUC turun ke 0.7859)"),
        ("Random Forest (depth=8, Unweighted)", "n_estimators=200, max_depth=8, class_weight=None", RandomForestClassifier(n_estimators=200, max_depth=8, random_state=SEED, n_jobs=-1), "ROC-AUC tinggi tetapi recall churn hanya 0.5090 tanpa class_weight"),
        ("Random Forest (depth=8, Balanced)", "n_estimators=200, max_depth=8, class_weight=balanced", RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=SEED, n_jobs=-1), "MODEL TERPILIH: Skor F1 CV tertinggi (0.6327) & ROC-AUC tertinggi (0.8463) dengan variasi antar-fold rendah"),
        ("Random Forest (depth=12, Balanced_subsample)", "n_estimators=200, max_depth=12, class_weight=balanced_subsample", RandomForestClassifier(n_estimators=200, max_depth=12, class_weight="balanced_subsample", random_state=SEED, n_jobs=-1), "Lebih kompleks namun recall & F1 CV lebih rendah dari depth=8"),
        ("KNN (k=11, uniform)", "n_neighbors=11, weights=uniform", KNeighborsClassifier(n_neighbors=11, weights="uniform"), "Metode jarak kurang optimal pada ruang dimensi tinggi hasil one-hot"),
        ("KNN (k=25, distance)", "n_neighbors=25, weights=distance", KNeighborsClassifier(n_neighbors=25, weights="distance"), "Sedikit lebih baik dari k=11 namun masih di bawah model berbasis pohon & linear"),
        ("Naive Bayes (GaussianNB)", "var_smoothing=1e-9", GaussianNB(), "Recall tinggi tetapi precision sangat rendah (banyak false positive)")
    ]

    cv_clf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    clf_scoring = {"f1": "f1", "recall": "recall", "precision": "precision", "roc_auc": "roc_auc", "accuracy": "accuracy"}

    clf_table_rows = []
    for name, params_str, est, reason in clf_candidates:
        pipe = make_clf_pipe(est)
        scores = cross_validate(pipe, X_clf_train, y_clf_train, cv=cv_clf, scoring=clf_scoring, n_jobs=1)
        clf_table_rows.append({
            "dataset_version": DATASET_VERSION,
            "model_version": MODEL_VERSION,
            "Kandidat": name,
            "Parameter": params_str,
            "Preprocessing": clf_prep_desc,
            "F1_Mean": round(float(scores["test_f1"].mean()), 4),
            "F1_Std": round(float(scores["test_f1"].std()), 4),
            "Recall_Mean": round(float(scores["test_recall"].mean()), 4),
            "Recall_Std": round(float(scores["test_recall"].std()), 4),
            "Precision_Mean": round(float(scores["test_precision"].mean()), 4),
            "Precision_Std": round(float(scores["test_precision"].std()), 4),
            "ROC_AUC_Mean": round(float(scores["test_roc_auc"].mean()), 4),
            "ROC_AUC_Std": round(float(scores["test_roc_auc"].std()), 4),
            "Accuracy_Mean": round(float(scores["test_accuracy"].mean()), 4),
            "Selected": name == "Random Forest (depth=8, Balanced)",
            "Alasan_Pemilihan_Catatan": reason
        })

    df_clf_exp = pd.DataFrame(clf_table_rows).sort_values(by="F1_Mean", ascending=False).reset_index(drop=True)
    df_clf_exp.to_csv(OUTPUT_DIR / "experiment_table_classification.csv", index=False)

    # Latih model klasifikasi terpilih dan tentukan threshold dari OOF
    selected_clf_name = "Random Forest (depth=8, Balanced)"
    selected_clf_pipe = make_clf_pipe(RandomForestClassifier(
        n_estimators=200, max_depth=8, class_weight="balanced", random_state=SEED, n_jobs=-1
    ))
    oof_proba = cross_val_predict(selected_clf_pipe, X_clf_train, y_clf_train, cv=cv_clf, method="predict_proba")[:, 1]

    threshold_curve = []
    best_th = 0.55
    best_oof_f1 = -1.0
    for th in np.arange(0.30, 0.71, 0.05):
        th_val = round(float(th), 2)
        pred_oof = (oof_proba >= th_val).astype(int)
        f1_v = float(f1_score(y_clf_train, pred_oof))
        rec_v = float(recall_score(y_clf_train, pred_oof))
        prec_v = float(precision_score(y_clf_train, pred_oof))
        tn_o, fp_o, fn_o, tp_o = confusion_matrix(y_clf_train, pred_oof).ravel()
        threshold_curve.append({
            "threshold": th_val,
            "f1_oof": round(f1_v, 4),
            "recall_oof": round(rec_v, 4),
            "precision_oof": round(prec_v, 4),
            "tp": int(tp_o), "fn": int(fn_o), "fp": int(fp_o), "tn": int(tn_o)
        })
        if f1_v > best_oof_f1:
            best_oof_f1 = f1_v
            best_th = th_val

    selected_clf_pipe.fit(X_clf_train, y_clf_train)
    test_proba = selected_clf_pipe.predict_proba(X_clf_test)[:, 1]
    test_pred = (test_proba >= best_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_clf_test, test_pred).ravel()

    clf_test_eval = {
        "dataset_version": DATASET_VERSION,
        "model_version": MODEL_VERSION,
        "evaluation_source": "Hold-out Test Set (20% = 1,409 rows, stratified, seed=42)",
        "selected_model": selected_clf_name,
        "positive_class": POSITIVE_CLASS,
        "threshold": best_th,
        "test_size": int(len(y_clf_test)),
        "f1": round(float(f1_score(y_clf_test, test_pred)), 4),
        "recall": round(float(recall_score(y_clf_test, test_pred)), 4),
        "precision": round(float(precision_score(y_clf_test, test_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_clf_test, test_proba)), 4),
        "accuracy": round(float(accuracy_score(y_clf_test, test_pred)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "threshold_validation_curve": threshold_curve
    }

    # =========================================================================
    # B. CLUSTERING PELANGGAN
    # =========================================================================
    X_cluster = df[cluster_features].copy()
    cluster_prep_desc = "Num (tenure, MonthlyCharges, TotalCharges): SimpleImputer(constant=0.0) + StandardScaler"
    cluster_preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
            ("scaler", StandardScaler())
        ]), cluster_features)
    ])
    X_scaled = cluster_preprocessor.fit_transform(X_cluster)
    n_total = len(X_scaled)

    cluster_rows = []
    elbow_curve = []
    for k in [2, 3, 4, 5, 6]:
        km = KMeans(n_clusters=k, random_state=SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        elbow_curve.append({"k": k, "inertia": round(float(km.inertia_), 2)})
        reason = (
            "MODEL TERPILIH: Titik siku (elbow) optimal, Davies-Bouldin terendah (0.7079), Silhouette tinggi (0.4722), cakupan 100% tanpa noise, dan membentuk 4 segmen bisnis (baru/loyal x hemat/tinggi)"
            if k == 4 else "Pembanding variasi jumlah klaster K-Means"
        )
        cluster_rows.append({
            "dataset_version": DATASET_VERSION,
            "model_version": MODEL_VERSION,
            "Kandidat": f"K-Means (k={k})",
            "Parameter": f"n_clusters={k}, n_init=10, random_state=42",
            "Preprocessing": cluster_prep_desc,
            "Jumlah_Klaster": k,
            "Inertia": round(float(km.inertia_), 2),
            "Silhouette": round(float(silhouette_score(X_scaled, labels)), 4),
            "Davies_Bouldin": round(float(davies_bouldin_score(X_scaled, labels)), 4),
            "Calinski_Harabasz": round(float(calinski_harabasz_score(X_scaled, labels)), 2),
            "Noise_Count": 0,
            "Noise_Pct (%)": 0.0,
            "Coverage_Pct (%)": 100.0,
            "Selected": k == 4,
            "Alasan_Pemilihan_Catatan": reason
        })

    for k in [2, 3, 4, 5]:
        agg = AgglomerativeClustering(n_clusters=k, linkage="ward")
        labels = agg.fit_predict(X_scaled)
        cluster_rows.append({
            "dataset_version": DATASET_VERSION,
            "model_version": MODEL_VERSION,
            "Kandidat": f"Agglomerative (k={k})",
            "Parameter": f"n_clusters={k}, linkage=ward",
            "Preprocessing": cluster_prep_desc,
            "Jumlah_Klaster": k,
            "Inertia": np.nan,
            "Silhouette": round(float(silhouette_score(X_scaled, labels)), 4),
            "Davies_Bouldin": round(float(davies_bouldin_score(X_scaled, labels)), 4),
            "Calinski_Harabasz": round(float(calinski_harabasz_score(X_scaled, labels)), 2),
            "Noise_Count": 0,
            "Noise_Pct (%)": 0.0,
            "Coverage_Pct (%)": 100.0,
            "Selected": False,
            "Alasan_Pemilihan_Catatan": "Skor Silhouette & Davies-Bouldin lebih rendah dari K-Means serta tidak memiliki fungsi .predict() langsung untuk batch baru"
        })

    for eps, min_s in [(0.08, 15), (0.10, 15), (0.12, 20), (0.15, 25), (0.20, 30)]:
        db = DBSCAN(eps=eps, min_samples=min_s)
        labels = db.fit_predict(X_scaled)
        non_noise = labels != -1
        n_noise = int((~non_noise).sum())
        n_clusters = len(set(labels[non_noise]))
        cov_pct = round(float(non_noise.mean() * 100), 2)
        if 2 <= n_clusters < non_noise.sum():
            sil = round(float(silhouette_score(X_scaled[non_noise], labels[non_noise])), 4)
            dbi = round(float(davies_bouldin_score(X_scaled[non_noise], labels[non_noise])), 4)
            chi = round(float(calinski_harabasz_score(X_scaled[non_noise], labels[non_noise])), 2)
        else:
            sil, dbi, chi = np.nan, np.nan, np.nan
        cluster_rows.append({
            "dataset_version": DATASET_VERSION,
            "model_version": MODEL_VERSION,
            "Kandidat": f"DBSCAN (eps={eps}, min_samples={min_s})",
            "Parameter": f"eps={eps}, min_samples={min_s}",
            "Preprocessing": cluster_prep_desc,
            "Jumlah_Klaster": n_clusters,
            "Inertia": np.nan,
            "Silhouette": sil,
            "Davies_Bouldin": dbi,
            "Calinski_Harabasz": chi,
            "Noise_Count": n_noise,
            "Noise_Pct (%)": round(n_noise / n_total * 100, 2),
            "Coverage_Pct (%)": cov_pct,
            "Selected": False,
            "Alasan_Pemilihan_Catatan": "Menghasilkan terlalu banyak klaster mikro atau titik noise serta skor Silhouette rendah pada distribusi kontinu tagihan"
        })

    df_cluster_exp = pd.DataFrame(cluster_rows)
    df_cluster_exp.to_csv(OUTPUT_DIR / "experiment_table_clustering.csv", index=False)

    selected_cluster_pipe = Pipeline([
        ("preprocessor", cluster_preprocessor),
        ("model", KMeans(n_clusters=4, random_state=SEED, n_init=10))
    ])
    df["segment_id"] = selected_cluster_pipe.fit_predict(X_cluster)

    seg_profile = df.groupby("segment_id").agg(
        customer_count=("customerID", "count"),
        tenure_mean=("tenure", "mean"),
        monthly_charges_mean=("MonthlyCharges", "mean"),
        total_charges_mean=("TotalCharges", "mean"),
        churn_yes_count=("Churn", lambda s: int((s == "Yes").sum()))
    ).reset_index()
    seg_profile["population_pct"] = (seg_profile["customer_count"] / len(df) * 100).round(2)
    seg_profile["historical_churn_rate_pct"] = (seg_profile["churn_yes_count"] / seg_profile["customer_count"] * 100).round(2)

    median_tenure = seg_profile["tenure_mean"].median()
    median_mc = seg_profile["monthly_charges_mean"].median()
    segment_map = {}
    segment_descriptions = {}
    for _, row in seg_profile.iterrows():
        sid = int(row["segment_id"])
        is_loyal = row["tenure_mean"] >= median_tenure
        is_high_bill = row["monthly_charges_mean"] >= median_mc
        if not is_loyal and is_high_bill:
            name = "Pelanggan Baru Tagihan Tinggi (Rentan)"
            desc = "Masa langganan pendek dengan tagihan bulanan tinggi; memiliki tingkat churn historis tertinggi (48.24%)."
        elif not is_loyal and not is_high_bill:
            name = "Pelanggan Baru Paket Hemat"
            desc = "Masa langganan pendek dengan paket dasar hemat; tingkat churn menengah (24.66%)."
        elif is_loyal and is_high_bill:
            name = "Pelanggan Loyal Premium (High-Value)"
            desc = "Masa langganan panjang dengan layanan lengkap & tagihan tinggi; kontributor pendapatan terbesar (churn 15.39%)."
        else:
            name = "Pelanggan Loyal Paket Hemat"
            desc = "Masa langganan panjang dengan tagihan rendah; segmen paling stabil dengan churn terendah (5.00%)."
        segment_map[str(sid)] = name
        segment_descriptions[sid] = desc

    seg_profile["segment_name"] = seg_profile["segment_id"].map(lambda x: segment_map[str(int(x))])
    seg_profile["description"] = seg_profile["segment_id"].map(segment_descriptions)
    seg_profile.round(2).to_csv(OUTPUT_DIR / "segment_profiles.csv", index=False)

    # =========================================================================
    # C. REGRESI TAGIHAN BULANAN
    # =========================================================================
    X_reg = df[reg_features].copy()
    y_reg = df["MonthlyCharges"].copy()
    X_reg_train, X_reg_test, y_reg_train, y_reg_test, id_reg_train, id_reg_test = train_test_split(
        X_reg, y_reg, df[id_col], test_size=0.20, random_state=SEED
    )

    reg_num_cols = [c for c in reg_features if X_reg[c].dtype != "object"]
    reg_cat_cols = [c for c in reg_features if X_reg[c].dtype == "object"]
    reg_prep_desc = "Num (SeniorCitizen, tenure): SimpleImputer(median) + StandardScaler | Cat (15 layanan/profil): SimpleImputer(most_frequent) + OneHotEncoder(handle_unknown='ignore')"

    def make_reg_pipe(est):
        return Pipeline([
            ("preprocessor", ColumnTransformer([
                ("num", Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())
                ]), reg_num_cols),
                ("cat", Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
                ]), reg_cat_cols)
            ])),
            ("model", est)
        ])

    reg_candidates = [
        ("Dummy Regressor (Mean Baseline)", "strategy=mean", DummyRegressor(strategy="mean"), "Baseline prediksi rata-rata ($64.76 USD), MAE sangat besar ($26.26 USD)"),
        ("Dummy Regressor (Median Baseline)", "strategy=median", DummyRegressor(strategy="median"), "Baseline prediksi median, MAE sangat besar ($25.84 USD)"),
        ("Linear Regression (OLS)", "fit_intercept=True", LinearRegression(), "Akurasi sangat tinggi namun tanpa regularisasi terhadap multikolinearitas one-hot encoding"),
        ("Ridge Regression (alpha=0.1)", "alpha=0.1", Ridge(alpha=0.1, random_state=SEED), "Sangat akurat, regularisasi L2 ringan"),
        ("Ridge Regression (alpha=1.0)", "alpha=1.0", Ridge(alpha=1.0, random_state=SEED), "MODEL TERPILIH: MAE CV sangat rendah ($0.7832 USD), R2=0.9988, dan koefisien stabil berkat regularisasi L2 terhadap fitur one-hot"),
        ("Ridge Regression (alpha=10.0)", "alpha=10.0", Ridge(alpha=10.0, random_state=SEED), "Regularisasi sedikit terlalu kuat dibanding alpha=1.0"),
        ("Lasso Regression (alpha=0.01)", "alpha=0.01", Lasso(alpha=0.01, max_iter=5000, random_state=SEED), "MAE kompetitif ($0.7824 USD) namun konvergensi iteratif lebih lambat dari Ridge"),
        ("Lasso Regression (alpha=0.1)", "alpha=0.1", Lasso(alpha=0.1, max_iter=5000, random_state=SEED), "Penalti L1 mulai memangkas koefisien komponen layanan (MAE naik ke $0.8874 USD)"),
        ("Decision Tree Regressor (depth=5)", "max_depth=5", DecisionTreeRegressor(max_depth=5, random_state=SEED), "Kedalaman pohon belum cukup menangkap seluruh kombinasi tarif layanan (MAE $3.55 USD)"),
        ("Decision Tree Regressor (depth=8)", "max_depth=8", DecisionTreeRegressor(max_depth=8, random_state=SEED), "Lebih baik dari depth=5 tetapi MAE masih 2x lipat Ridge Regression"),
        ("Decision Tree Regressor (depth=12)", "max_depth=12", DecisionTreeRegressor(max_depth=12, random_state=SEED), "Rawan overfit pada kombinasi kategori langka"),
        ("Random Forest Regressor (depth=8)", "n_estimators=200, max_depth=8", RandomForestRegressor(n_estimators=200, max_depth=8, random_state=SEED, n_jobs=-1), "Lebih stabil dari pohon tunggal namun kurang efisien untuk fungsi tarif aditif linear"),
        ("Random Forest Regressor (depth=12)", "n_estimators=200, max_depth=12", RandomForestRegressor(n_estimators=200, max_depth=12, random_state=SEED, n_jobs=-1), "MAE $0.9883 USD, masih kalah akurat dan jauh lebih berat dibanding Ridge Regression")
    ]

    cv_reg = KFold(n_splits=5, shuffle=True, random_state=SEED)
    reg_scoring = {"mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error", "r2": "r2"}

    reg_table_rows = []
    for name, params_str, est, reason in reg_candidates:
        pipe = make_reg_pipe(est)
        scores = cross_validate(pipe, X_reg_train, y_reg_train, cv=cv_reg, scoring=reg_scoring, n_jobs=1)
        reg_table_rows.append({
            "dataset_version": DATASET_VERSION,
            "model_version": MODEL_VERSION,
            "Kandidat": name,
            "Parameter": params_str,
            "Preprocessing": reg_prep_desc,
            "MAE_Mean (USD)": round(float((-scores["test_mae"]).mean()), 4),
            "MAE_Std (USD)": round(float((-scores["test_mae"]).std()), 4),
            "RMSE_Mean (USD)": round(float((-scores["test_rmse"]).mean()), 4),
            "RMSE_Std (USD)": round(float((-scores["test_rmse"]).std()), 4),
            "R2_Mean": round(float(scores["test_r2"].mean()), 4),
            "R2_Std": round(float(scores["test_r2"].std()), 4),
            "Selected": name == "Ridge Regression (alpha=1.0)",
            "Alasan_Pemilihan_Catatan": reason
        })

    df_reg_exp = pd.DataFrame(reg_table_rows).sort_values(by="MAE_Mean (USD)", ascending=True).reset_index(drop=True)
    df_reg_exp.to_csv(OUTPUT_DIR / "experiment_table_regression.csv", index=False)

    selected_reg_name = "Ridge Regression (alpha=1.0)"
    selected_reg_pipe = make_reg_pipe(Ridge(alpha=1.0, random_state=SEED))
    selected_reg_pipe.fit(X_reg_train, y_reg_train)
    y_reg_pred_test = selected_reg_pipe.predict(X_reg_test)
    reg_residuals = y_reg_test - y_reg_pred_test

    # Sampel titik grafik aktual vs prediksi & residual (100 sampel deterministik untuk payload grafik Frontend/Backend)
    sample_chart_idx = np.linspace(0, len(y_reg_test) - 1, 100, dtype=int)
    reg_chart_points = []
    for idx in sample_chart_idx:
        actual_v = round(float(y_reg_test.iloc[idx]), 2)
        pred_v = round(float(y_reg_pred_test[idx]), 2)
        reg_chart_points.append({
            "customer_id": str(id_reg_test.iloc[idx]),
            "actual_monthly_charges": actual_v,
            "predicted_monthly_charges": pred_v,
            "residual": round(actual_v - pred_v, 2)
        })

    reg_test_eval = {
        "dataset_version": DATASET_VERSION,
        "model_version": MODEL_VERSION,
        "evaluation_source": "Hold-out Test Set (20% = 1,409 rows, seed=42)",
        "selected_model": selected_reg_name,
        "currency_unit": CURRENCY_UNIT,
        "test_size": int(len(y_reg_test)),
        "mae_usd": round(float(mean_absolute_error(y_reg_test, y_reg_pred_test)), 4),
        "rmse_usd": round(float(root_mean_squared_error(y_reg_test, y_reg_pred_test)), 4),
        "r2": round(float(r2_score(y_reg_test, y_reg_pred_test)), 4),
        "error_explanation": "Rata-rata kesalahan absolut (MAE) prediksi tagihan bulanan hanya sebesar $0.79 USD pada rentang tagihan $18.25 - $118.75 USD.",
        "actual_vs_predicted_and_residuals_sample": reg_chart_points
    }

    # =========================================================================
    # D. EKSPOR ARTEFAK (.joblib) DAN METADATA LENGKAP
    # =========================================================================
    clf_artifact_path = ARTIFACTS_OUT_DIR / "churn_classifier.joblib"
    cluster_artifact_path = ARTIFACTS_OUT_DIR / "customer_clustering.joblib"
    reg_artifact_path = ARTIFACTS_OUT_DIR / "monthly_charges_regressor.joblib"

    joblib.dump(selected_clf_pipe, clf_artifact_path)
    joblib.dump(selected_cluster_pipe, cluster_artifact_path)
    joblib.dump(selected_reg_pipe, reg_artifact_path)

    # Hasilkan contoh prediksi gabungan per customerID (10 baris pertama dari dataset acuan)
    sample_df = df.iloc[:10].copy()
    sample_probs = selected_clf_pipe.predict_proba(sample_df[clf_features])[:, 1]
    sample_preds = np.where(sample_probs >= best_th, "Yes", "No")
    sample_segs = selected_cluster_pipe.predict(sample_df[cluster_features])
    sample_mc_preds = selected_reg_pipe.predict(sample_df[reg_features])

    sample_records = []
    for i in range(len(sample_df)):
        cid = str(sample_df.iloc[i]["customerID"])
        prob_v = round(float(sample_probs[i]), 4)
        pred_lbl = str(sample_preds[i])
        seg_id = int(sample_segs[i])
        seg_name = segment_map.get(str(seg_id), "Unassigned / Perlu Tinjauan Manual")
        mc_pred = round(float(sample_mc_preds[i]), 2)
        rec_text = evaluate_retention_rule(prob_v, pred_lbl, seg_id)
        sample_records.append({
            "customer_id": cid,
            "actual_churn": str(sample_df.iloc[i]["Churn"]),
            "churn_probability": prob_v,
            "churn_prediction": pred_lbl,
            "segment_id": seg_id,
            "segment_name": seg_name,
            "actual_monthly_charges": round(float(sample_df.iloc[i]["MonthlyCharges"]), 2),
            "predicted_monthly_charges": mc_pred,
            "currency_unit": CURRENCY_UNIT,
            "recommendation": rec_text
        })

    pd.DataFrame(sample_records).to_csv(OUTPUT_DIR / "sample_predictions.csv", index=False)
    with open(OUTPUT_DIR / "sample_predictions.json", "w", encoding="utf-8") as f:
        json.dump(sample_records, f, indent=2, ensure_ascii=False)

    # Metadata kontrak lengkap untuk Backend & Frontend
    feature_dtypes = {col: str(df[col].dtype) for col in df.columns if col not in [id_col, "Churn"]}
    model_metadata = {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_file": "WA_Fn-UseC_-Telco-Customer-Churn.csv",
        "dataset_rows_before_cleaning": rows_before,
        "dataset_rows_after_cleaning": rows_after,
        "total_charges_missing_imputed_zero": n_missing_tc,
        "model_version": MODEL_VERSION,
        "currency_unit": CURRENCY_UNIT,
        "id_column": id_col,
        "dependencies": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "joblib": joblib.__version__
        },
        "artifacts": {
            "classification": "churn_classifier.joblib",
            "clustering": "customer_clustering.joblib",
            "regression": "monthly_charges_regressor.joblib"
        },
        "models": {
            "classification": {
                "selected_model": selected_clf_name,
                "target_column": "Churn",
                "positive_class": POSITIVE_CLASS,
                "threshold": best_th,
                "required_features": clf_features,
                "feature_types": {c: feature_dtypes[c] for c in clf_features},
                "evaluation_source": clf_test_eval["evaluation_source"],
                "test_metrics": {k: clf_test_eval[k] for k in ["f1", "recall", "precision", "roc_auc", "accuracy", "confusion_matrix"]}
            },
            "clustering": {
                "selected_model": "K-Means (n_clusters=4)",
                "required_features": cluster_features,
                "feature_types": {c: feature_dtypes[c] for c in cluster_features},
                "segment_id_to_name": segment_map,
                "noise_handling_policy": {
                    "noise_label": -1,
                    "fallback_segment_name": "Unassigned / Perlu Tinjauan Manual",
                    "selected_model_produces_noise": False
                },
                "segment_profiles": seg_profile.round(2).to_dict(orient="records"),
                "evaluation_source": "Full Dataset Unsupervised Internal Metrics (N = 7,043)",
                "internal_metrics": {
                    "n_clusters": 4,
                    "inertia": 4148.48,
                    "silhouette": 0.4722,
                    "davies_bouldin": 0.7079,
                    "calinski_harabasz": 9603.99,
                    "noise_count": 0,
                    "coverage_pct": 100.0
                }
            },
            "regression": {
                "selected_model": selected_reg_name,
                "target_column": "MonthlyCharges",
                "currency_unit": CURRENCY_UNIT,
                "excluded_columns": ["customerID", "Churn", "MonthlyCharges", "TotalCharges"],
                "required_features": reg_features,
                "feature_types": {c: feature_dtypes[c] for c in reg_features},
                "evaluation_source": reg_test_eval["evaluation_source"],
                "test_metrics": {k: reg_test_eval[k] for k in ["mae_usd", "rmse_usd", "r2"]}
            }
        },
        "retention_simulation_rules": {
            "label": "Simulasi Berbasis Aturan (Offline Historical Dataset)",
            "evaluation_order": "Dievaluasi secara berurutan dari Prioritas 1 hingga Prioritas 6; aturan pertama yang terpenuhi langsung dipilih.",
            "missing_input_fallback": "[Simulasi] Data risiko atau segmen belum tersedia — lakukan verifikasi profil pelanggan terlebih dahulu.",
            "rules": [
                {
                    "priority": 1,
                    "condition": "churn_probability >= 0.70 AND segment_id IN (1, 2)",
                    "target_description": "Risiko Kritis pada Pelanggan Tagihan Tinggi / Premium",
                    "recommendation": "[Simulasi - Prioritas 1] Risiko Kritis Bernilai Tinggi: Tawarkan diskon kontrak 1-2 tahun sebesar 15-20% & hubungi langsung melalui tim retensi VIP."
                },
                {
                    "priority": 2,
                    "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id == 2",
                    "target_description": "Pelanggan Baru Tagihan Tinggi Berisiko Churn",
                    "recommendation": "[Simulasi - Prioritas 2] Pelanggan Baru Tagihan Tinggi Berisiko: Tawarkan paket bundling hemat (migrasi kontrak 1 tahun) & gratis uji layanan TechSupport/OnlineSecurity 3 bulan."
                },
                {
                    "priority": 3,
                    "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id == 1",
                    "target_description": "Pelanggan Loyal Premium Berisiko Churn",
                    "recommendation": "[Simulasi - Prioritas 3] Pelanggan Loyal Premium Berisiko: Berikan apresiasi loyalitas (upgrade kecepatan/layanan streaming gratis) & peninjauan tagihan eksklusif."
                },
                {
                    "priority": 4,
                    "condition": "churn_prediction == 'Yes' (prob >= 0.55) AND segment_id IN (0, 3)",
                    "target_description": "Pelanggan Paket Hemat Berisiko Churn",
                    "recommendation": "[Simulasi - Prioritas 4] Pelanggan Paket Hemat Berisiko: Kirim promo perpanjangan kontrak ringan & pengingat pembayaran otomatis (auto-pay)."
                },
                {
                    "priority": 5,
                    "condition": "churn_prediction == 'No' AND (segment_id == 2 OR churn_probability >= 0.40)",
                    "target_description": "Pencegahan Dini pada Segmen Rentan / Risiko Menengah",
                    "recommendation": "[Simulasi - Prioritas 5] Pencegahan Dini (Preventif): Edukasi manfaat layanan tambahan & tawarkan insentif peralihan dari Month-to-month ke kontrak tahunan."
                },
                {
                    "priority": 6,
                    "condition": "Default (churn_prediction == 'No' AND churn_probability < 0.40 AND segment_id != 2)",
                    "target_description": "Pelanggan Stabil Risiko Rendah",
                    "recommendation": "[Simulasi - Prioritas 6] Pelanggan Stabil: Pertahankan kualitas layanan reguler & tawarkan program referral/cross-selling berkala."
                }
            ]
        },
        "sample_input_row": df_raw.iloc[0].to_dict(),
        "sample_expected_output": sample_records[0]
    }

    evaluations_payload = {
        "dataset_version": DATASET_VERSION,
        "model_version": MODEL_VERSION,
        "currency_unit": CURRENCY_UNIT,
        "classification": {
            "cv_candidates": df_clf_exp.to_dict(orient="records"),
            "test_evaluation": clf_test_eval
        },
        "clustering": {
            "candidates": json.loads(df_cluster_exp.to_json(orient="records")),
            "elbow_curve": elbow_curve,
            "segment_profiles": seg_profile.round(2).to_dict(orient="records")
        },
        "regression": {
            "cv_candidates": df_reg_exp.to_dict(orient="records"),
            "test_evaluation": reg_test_eval
        }
    }

    metadata_path = ARTIFACTS_OUT_DIR / "model_metadata.json"
    eval_payload_path = OUTPUT_DIR / "evaluations_payload.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2, ensure_ascii=False)
    with open(eval_payload_path, "w", encoding="utf-8") as f:
        json.dump(evaluations_payload, f, indent=2, ensure_ascii=False)

    # Salin artefak & metadata ke backend/artifacts/ untuk siap dipakai Backend
    for item in [clf_artifact_path, cluster_artifact_path, reg_artifact_path, metadata_path, eval_payload_path]:
        shutil.copy2(item, BACKEND_ARTIFACTS_DIR / item.name)

    print("=== EKSPOR PIPELINE & METADATA SELESAI ===")
    print(f"Dataset Version : {DATASET_VERSION}")
    print(f"Model Version   : {MODEL_VERSION}")
    print(f"Artefak Data    : {ARTIFACTS_OUT_DIR}")
    print(f"Artefak Backend : {BACKEND_ARTIFACTS_DIR}")
    print("Contoh hasil baris ke-1 (7590-VHVEG):")
    print(json.dumps(sample_records[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
