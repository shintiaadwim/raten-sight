# Dokumen Serah Terima Role Data (RetenSight)

Dokumen ini memenuhi checklist **Ekspor dan serah terima Data** pada [docs/jobdesk.md](../docs/jobdesk.md#L52-L60).

---

## 1. Identitas Dataset, Model, dan Versi Dependensi

| Atribut | Nilai |
| --- | --- |
| **Dataset ID** | `ibm-telco-customer-churn` |
| **Versi Dataset (`dataset_version`)** | `telco-churn-v1.0` |
| **File Dataset Berversi** | `data/outputs/telco-churn-v1.0.csv` (salinan dari `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`) |
| **Versi Model (`model_version`)** | `retensight-models-v1.0` |
| **Satuan Biaya (`currency_unit`)** | `USD` (`$`) |
| **Python** | `3.12.9` |
| **NumPy / pandas / scikit-learn / joblib** | `numpy==2.2.6`, `pandas==2.2.3`, `scikit-learn==1.6.1`, `joblib==1.4.2` |

---

## 2. Perintah Reproducible (Cleaning, Pelatihan, Evaluasi, Ekspor, dan Verifikasi)

Seluruh proses dari cleaning, CV 5-Fold, evaluasi data uji, hingga ekspor `.joblib` dan metadata dapat dijalankan ulang melalui satu perintah dari root repositori:

```powershell
# 1. Jalankan cleaning, eksperimen, evaluasi, dan ekspor artefak
.\.venv\Scripts\python.exe data/run_pipeline.py

# 2. Verifikasi muat ulang artefak pada proses Python baru (mencocokkan 10 baris contoh)
.\.venv\Scripts\python.exe data/verify_artifacts.py
```

---

## 3. Tiga Tabel Eksperimen & Alasan Pemilihan Model

File lengkap dalam format CSV dan JSON tersedia di:
- [experiment_table_classification.csv](outputs/experiment_table_classification.csv)
- [experiment_table_clustering.csv](outputs/experiment_table_clustering.csv)
- [experiment_table_regression.csv](outputs/experiment_table_regression.csv)
- [evaluations_payload.json](outputs/evaluations_payload.json)

### A. Tabel Eksperimen 1 — Klasifikasi Churn (`Churn = Yes` sebagai Kelas Positif)
- **Preprocessing di setiap fold CV:**
  - Numerik (`SeniorCitizen`, `tenure`, `MonthlyCharges`, `TotalCharges`): `SimpleImputer(strategy='constant', fill_value=0.0)` + `StandardScaler()`
  - Kategorikal (15 kolom): `SimpleImputer(strategy='most_frequent')` + `OneHotEncoder(handle_unknown='ignore')`

| Kandidat | Parameter | F1 CV (Mean ± Std) | Recall CV | Precision CV | ROC-AUC CV | Catatan / Alasan Pemilihan |
| --- | --- | --- | --- | --- | --- | --- |
| **Random Forest (depth=8, Balanced)** ✅ | `n_estimators=200, max_depth=8, class_weight=balanced` | **0,6327 ± 0,0144** | 0,7579 | 0,5432 | **0,8463 ± 0,0093** | **MODEL TERPILIH:** F1 & ROC-AUC tertinggi dengan variasi antar-fold rendah |
| Logistic Regression (Balanced, C=0.1) | `C=0.1, class_weight=balanced` | 0,6295 ± 0,0209 | 0,7980 | 0,5199 | 0,8455 ± 0,0119 | Peringkat ke-2; recall tinggi namun precision lebih rendah |
| Logistic Regression (Balanced, C=1.0) | `C=1.0, class_weight=balanced` | 0,6283 ± 0,0232 | 0,8013 | 0,5169 | 0,8460 ± 0,0124 | Kompetitif, sedikit di bawah C=0.1 dan RF depth=8 |
| Random Forest (depth=12, Balanced_subsample) | `n_estimators=200, max_depth=12, class_weight=balanced_subsample` | 0,6206 ± 0,0208 | 0,6401 | 0,6029 | 0,8383 ± 0,0096 | Lebih kompleks tetapi recall turun dibanding depth=8 |
| Decision Tree (depth=5, Balanced) | `max_depth=5, class_weight=balanced` | 0,6152 ± 0,0099 | 0,7773 | 0,5097 | 0,8276 ± 0,0128 | Pohon tunggal; F1 dan ROC-AUC di bawah ansambel RF |
| Naive Bayes (GaussianNB) | `var_smoothing=1e-9` | 0,5974 ± 0,0093 | 0,8482 | 0,4612 | 0,8212 ± 0,0119 | Terlalu banyak false positive (precision 0,4612) |
| Logistic Regression (Unweighted, C=1.0) | `C=1.0, class_weight=None` | 0,5923 ± 0,0299 | 0,5431 | 0,6529 | 0,8462 ± 0,0126 | Tanpa `class_weight`, recall churn rendah (0,5431) |
| KNN (k=25, distance) | `n_neighbors=25, weights=distance` | 0,5794 ± 0,0139 | 0,5639 | 0,5958 | 0,8143 ± 0,0097 | Kurang optimal pada ruang fitur one-hot berdimensi tinggi |
| Dummy (Uniform Baseline) | `strategy=uniform` | 0,3522 ± 0,0128 | 0,5070 | 0,2699 | 0,5000 ± 0,0000 | Baseline tebakan acak 50:50 |
| Dummy (Stratified Baseline) | `strategy=stratified` | 0,2762 ± 0,0249 | 0,2776 | 0,2748 | 0,5065 ± 0,0171 | Baseline acak proporsional |

- **Threshold Akhir (`0,55`) & Evaluasi Data Uji (20% = 1.409 baris):**
  - **F1 = `0,6253`**, **Recall = `0,7139`**, **Precision = `0,5563`**, **ROC-AUC = `0,8416`**, **Accuracy = `0,7729`**
  - **Confusion Matrix Data Uji:** `TP = 267`, `FN = 107`, `FP = 213`, `TN = 822`.

---

### B. Tabel Eksperimen 2 — Clustering Pelanggan (`tenure`, `MonthlyCharges`, `TotalCharges`)
- **Preprocessing:** `SimpleImputer(strategy='constant', fill_value=0.0)` + `StandardScaler()`

| Kandidat | Parameter | Klaster | Inertia | Silhouette | Davies–Bouldin | Calinski–Harabasz | Noise (%) | Cakupan (%) | Alasan Pemilihan |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-Means (k=2) | `n_clusters=2` | 2 | 9.712,11 | 0,4797 | 0,7797 | 8.276,91 | 0,0% | 100,0% | Terlalu umum (hanya membagi 2 kelompok besar) |
| K-Means (k=3) | `n_clusters=3` | 3 | 6.186,19 | 0,4515 | 0,8541 | 8.502,61 | 0,0% | 100,0% | Davies–Bouldin memburuk dibanding k=4 |
| **K-Means (k=4)** ✅ | `n_clusters=4` | **4** | **4.148,48** | **0,4722** | **0,7079** | **9.603,99** | **0,0%** | **100,0%** | **MODEL TERPILIH:** Titik elbow terbaik, Davies–Bouldin terendah (0,7079), 0% noise, dan membentuk 4 segmen bisnis yang jelas |
| K-Means (k=5) | `n_clusters=5` | 5 | 3.111,40 | 0,4437 | 0,7580 | 10.189,01 | 0,0% | 100,0% | Silhouette turun ke 0,4437 |
| Agglomerative (k=4) | `n_clusters=4, linkage=ward` | 4 | — | 0,3821 | 0,8731 | 7.225,91 | 0,0% | 100,0% | Silhouette lebih rendah & tidak mendukung `.predict()` langsung |
| DBSCAN (eps=0.12, min=20) | `eps=0.12, min_samples=20` | 13 | — | 0,1459 | 0,7778 | 1.730,25 | 15,16% | 84,84% | Terpecah menjadi 13 klaster kecil dan 1.068 baris noise |

- **Pemetaan ID Segmen & Profil Segmen (`K-Means k=4`):**
  - `0` → **`Pelanggan Baru Paket Hemat`** (`1.703` pelanggan / `24,18%`, rata-rata `tenure = 10,21` bln, `MonthlyCharges = $31,78`, *historical churn rate* = **`24,66%`**)
  - `1` → **`Pelanggan Loyal Premium (High-Value)`** (`1.904` pelanggan / `27,03%`, rata-rata `tenure = 59,53` bln, `MonthlyCharges = $93,31`, *historical churn rate* = **`15,39%`**)
  - `2` → **`Pelanggan Baru Tagihan Tinggi (Rentan)`** (`2.276` pelanggan / `32,32%`, rata-rata `tenure = 15,42` bln, `MonthlyCharges = $80,78`, *historical churn rate* = **`48,24%`**)
  - `3` → **`Pelanggan Loyal Paket Hemat`** (`1.160` pelanggan / `16,47%`, rata-rata `tenure = 53,57` bln, `MonthlyCharges = $34,91`, *historical churn rate* = **`5,00%`**)
  - **Perlakuan Noise (`-1`):** Model terpilih (`K-Means k=4`) tidak menghasilkan titik *noise* (`0%`). Jika ada label `-1`, dipetakan ke `"Unassigned / Perlu Tinjauan Manual"`.

---

### C. Tabel Eksperimen 3 — Regresi Tagihan Bulanan (`MonthlyCharges` dalam USD `$`)
- **Fitur Input (17 kolom):** seluruh kolom kecuali `customerID`, `Churn`, `MonthlyCharges`, dan `TotalCharges`.

| Kandidat | Parameter | MAE CV (USD) | RMSE CV (USD) | $R^2$ CV | Catatan / Alasan Pemilihan |
| --- | --- | --- | --- | --- | --- |
| **Ridge Regression (alpha=1.0)** ✅ | `alpha=1.0` | **`$0,7832 ± $0,0269`** | **`$1,0219 ± $0,0338`** | **`0,9988 ± 0,0001`** | **MODEL TERPILIH:** Kesalahan rata-rata hanya `$0,78` USD dan stabil terhadap multikolinearitas one-hot encoding |
| Lasso Regression (alpha=0.01) | `alpha=0.01` | `$0,7824 ± $0,0263` | `$1,0216 ± $0,0329` | `0,9988 ± 0,0001` | Akurasi setara Ridge namun konvergensi koordinat lebih lambat |
| Linear Regression (OLS) | `fit_intercept=True` | `$0,7832 ± $0,0268` | `$1,0219 ± $0,0337` | `0,9988 ± 0,0001` | Tanpa regularisasi pada matriks fitur one-hot |
| Random Forest Regressor (depth=12) | `n_estimators=200, max_depth=12` | `$0,9883 ± $0,0413` | `$1,3594 ± $0,0623` | `0,9979 ± 0,0002` | Lebih berat & MAE lebih besar dibanding Ridge |
| Decision Tree Regressor (depth=8) | `max_depth=8` | `$1,5470 ± $0,0683` | `$2,2815 ± $0,0947` | `0,9942 ± 0,0005` | Kesalahan 2x lipat Ridge |
| Dummy Regressor (Mean Baseline) | `strategy=mean` | `$26,2607 ± $0,3245` | `$30,0906 ± $0,3365` | `-0,0011` | Baseline tebakan rata-rata (`$64,76` USD) |

- **Evaluasi Akhir Data Uji (20% = 1.409 baris):**
  - **MAE = `$0,7893` USD**, **RMSE = `$1,0515` USD**, **$R^2 = 0,9988$**.

---

## 4. Aturan Simulasi Retensi (Berurutan Berdasarkan Prioritas)

Aturan dievaluasi secara berurutan dari **Prioritas 1 sampai Prioritas 6**; aturan pertama yang memenuhi kondisi langsung dipilih:

1. **Prioritas 1 (`churn_probability >= 0.70` DAN `segment_id IN (1, 2)`):**
   - `"[Simulasi - Prioritas 1] Risiko Kritis Bernilai Tinggi: Tawarkan diskon kontrak 1-2 tahun sebesar 15-20% & hubungi langsung melalui tim retensi VIP."`
2. **Prioritas 2 (`churn_prediction == 'Yes'` DAN `segment_id == 2`):**
   - `"[Simulasi - Prioritas 2] Pelanggan Baru Tagihan Tinggi Berisiko: Tawarkan paket bundling hemat (migrasi kontrak 1 tahun) & gratis uji layanan TechSupport/OnlineSecurity 3 bulan."`
3. **Prioritas 3 (`churn_prediction == 'Yes'` DAN `segment_id == 1`):**
   - `"[Simulasi - Prioritas 3] Pelanggan Loyal Premium Berisiko: Berikan apresiasi loyalitas (upgrade kecepatan/layanan streaming gratis) & peninjauan tagihan eksklusif."`
4. **Prioritas 4 (`churn_prediction == 'Yes'` DAN `segment_id IN (0, 3)`):**
   - `"[Simulasi - Prioritas 4] Pelanggan Paket Hemat Berisiko: Kirim promo perpanjangan kontrak ringan & pengingat pembayaran otomatis (auto-pay)."`
5. **Prioritas 5 (`churn_prediction == 'No'` DAN (`segment_id == 2` ATAU `churn_probability >= 0.40`)):**
   - `"[Simulasi - Prioritas 5] Pencegahan Dini (Preventif): Edukasi manfaat layanan tambahan & tawarkan insentif peralihan dari Month-to-month ke kontrak tahunan."`
6. **Prioritas 6 (Default — pelanggan stabil risiko rendah):**
   - `"[Simulasi - Prioritas 6] Pelanggan Stabil: Pertahankan kualitas layanan reguler & tawarkan program referral/cross-selling berkala."`
- **Fallback jika input belum tersedia (`None` / `NaN`):**
  - `"[Simulasi] Data risiko atau segmen belum tersedia — lakukan verifikasi profil pelanggan terlebih dahulu."`

---

## 5. Daftar File Artefak & Output Serah Terima

- **Artefak Model & Metadata (`data/outputs/artifacts/` dan disalin ke `backend/artifacts/`):**
  - `churn_classifier.joblib`
  - `customer_clustering.joblib`
  - `monthly_charges_regressor.joblib`
  - [model_metadata.json](outputs/artifacts/model_metadata.json)
- **Hasil Evaluasi & Contoh Prediksi per `customerID` (`data/outputs/`):**
  - [evaluations_payload.json](outputs/evaluations_payload.json)
  - [sample_predictions.json](outputs/sample_predictions.json) & [sample_predictions.csv](outputs/sample_predictions.csv)
