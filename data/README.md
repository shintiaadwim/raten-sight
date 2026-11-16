# Panduan Data dan Machine Learning

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
