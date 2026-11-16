# Panduan Data dan Machine Learning

Folder ini berisi dependensi untuk pengolahan data, EDA, training offline, evaluasi, dan ekspor model. Tim Data bertanggung jawab atas kualitas dataset, pemilihan fitur, preprocessing, interpretasi segmen, serta aturan rekomendasi retensi. Petunjuk memasang dependensi ada di [README utama](../README.md#menjalankan-scaffold).

## Tugas pertama

Unduh CSV IBM Telco Customer Churn dan buat notebook EDA awal serta kamus data. Catat jumlah baris dan kolom, distribusi churn, nilai kosong pada `TotalCharges`, dan kategori khusus seperti `No internet service`. Bagikan temuan serta usulan kolom dan tipe input kepada Backend sebelum training baseline.

## Urutan pengerjaan

1. Unduh [IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn). Simpan `WA_Fn-UseC_-Telco-Customer-Churn.csv` di `data/raw/`.
2. Buat notebook EDA dan kamus data. Periksa 7.043 baris, 21 kolom, distribusi churn, dan nilai kosong pada `TotalCharges`. Dokumentasikan keputusan cleaning dan penanganan kategori.
3. Buat baseline Logistic Regression, K-Means, dan Linear Regression atau Ridge. Tambahkan model dummy dan bandingkan algoritma sesuai brief.
4. Untuk model supervisi, mulai dengan split 80:20 dan seed tetap. Stratifikasi klasifikasi berdasarkan `Churn`. Fit preprocessing di setiap fold dan gunakan data uji setelah pemilihan model. Gunakan CV lima fold pada data latih.
5. Simpan hasil eksperimen di `data/outputs/`. Setelah tim memilih model, serahkan pipeline dan metadata untuk dipasang Backend di `backend/artifacts/`. Rinciannya ada di [usulan kontrak integrasi](../docs/api.md).

| Tugas | Evaluasi yang direncanakan |
| --- | --- |
| Klasifikasi | Recall churn, precision, F1, ROC-AUC, confusion matrix |
| Clustering | Elbow atau inertia untuk K-Means, silhouette, Davies-Bouldin, Calinski-Harabasz, interpretasi profil |
| Regresi | MAE, RMSE, R², plot aktual versus prediksi dan residual |

Bandingkan baseline klasifikasi dengan Dummy Classifier, Decision Tree, Random Forest, KNN, dan Naive Bayes. Uji `class_weight` pada algoritma yang mendukungnya. Untuk clustering, bandingkan K-Means dengan Agglomerative dan DBSCAN. Untuk regresi, tambahkan Dummy Regressor, Decision Tree, dan Random Forest.

Pasang Jupyter sesuai kebutuhan untuk menjalankan notebook. Folder data mentah dan hasil eksperimen diabaikan Git.

## Hasil serah terima

- Notebook EDA, kamus data, serta skrip cleaning, training, dan evaluasi yang dapat dijalankan ulang.
- Metrik dan grafik eksperimen, termasuk perbandingan dengan baseline dan alasan pemilihan model akhir.
- Pipeline terpilih lengkap dengan preprocessing, daftar dan tipe fitur, versi artefak dan dependensi, threshold churn, serta contoh input dan output.
- Pemetaan ID ke nama segmen, profil setiap segmen, dan aturan retensi yang dapat diterapkan oleh Backend.
