# Panduan Data dan Machine Learning

Folder ini berisi dependensi untuk pengolahan data, EDA, training offline, evaluasi, dan ekspor model. Tim Data bertanggung jawab atas preprocessing, pelatihan dan perbandingan algoritma, pemilihan model, interpretasi segmen, serta aturan rekomendasi retensi. Backend menjalankan pipeline terpilih pada file churn yang dipasang di server. Frontend menampilkan hasil dan evaluasi melalui API. Petunjuk memasang dependensi ada di [README utama](../README.md#menjalankan-scaffold).

## Tugas pertama

Mulai dari file CSV IBM Telco Customer Churn yang disiapkan untuk proyek. Buat notebook EDA awal serta kamus data. Catat jumlah baris dan kolom, distribusi churn, nilai kosong pada `TotalCharges`, dan kategori khusus seperti `No internet service`. Bagikan versi dataset, temuan, dan skema fitur per model kepada Backend sebelum training baseline.

## Urutan pengerjaan

1. Simpan `WA_Fn-UseC_-Telco-Customer-Churn.csv` di `data/raw/` dan catat versi sumber yang akan dipakai untuk training dan dashboard. [Sumber dataset IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
2. Buat notebook EDA dan kamus data. Periksa 7.043 baris, 21 kolom, distribusi churn, dan nilai kosong pada `TotalCharges`. Dokumentasikan keputusan cleaning dan penanganan kategori.
3. Jalankan model pembanding awal, lalu lakukan perbandingan dan pemilihan model sesuai rencana eksperimen di bawah.
4. Simpan hasil eksperimen di `data/outputs/`. Setelah tim memilih model, serahkan salinan dataset berversi, pipeline untuk `backend/artifacts/`, dan metadata evaluasi. Sertakan contoh hasil berdasarkan `customerID` agar Backend dapat memeriksa pemrosesan batch. Rinciannya ada di [usulan kontrak integrasi](../docs/api.md).

## Rencana perbandingan algoritma

### Protokol evaluasi

- Catat versi dataset, daftar fitur, keputusan cleaning, versi dependensi, seed, dan parameter setiap kandidat. Keluarkan `customerID` dari semua fitur dan pertahankan ID untuk mencocokkan hasil dengan baris asal.
- Untuk klasifikasi dan regresi, gunakan pembagian 80:20 dengan seed tetap. Stratifikasi klasifikasi berdasarkan `Churn`. Gunakan pembagian dan fold yang sama untuk semua kandidat dalam tugas yang sama.
- Lakukan perbandingan dan tuning melalui CV lima fold pada data latih. Gunakan stratified CV untuk klasifikasi. Fit imputasi, encoding, dan scaling di bagian latih setiap fold melalui pipeline. Simpan data uji untuk evaluasi akhir model terpilih.
- Gunakan metrik, pembagian data, dan aturan perbandingan yang tercatat sebelum membaca hasil uji. Laporkan rerata dan simpangan baku skor CV agar variasi antar-fold terlihat.

### Klasifikasi churn

- **Target.** `Churn`, dengan `Yes` sebagai kelas positif.
- **Kandidat.** Dummy Classifier sebagai baseline minimum, Logistic Regression, Decision Tree, Random Forest, KNN, dan Naive Bayes.
- **Eksperimen.** Bandingkan kedalaman pohon, jumlah tetangga KNN, dan pengaturan regularisasi jika relevan. Uji `class_weight` pada algoritma yang mendukungnya. Jika resampling diperlukan, lakukan di bagian latih setiap fold.
- **Usulan pemilihan.** Gunakan F1 kelas churn sebagai metrik utama CV dengan aturan threshold yang sama untuk membandingkan kandidat. Tinjau recall, precision, dan ROC-AUC untuk memahami komprominya. Tentukan threshold akhir dari prediksi validasi model terpilih, lalu catat threshold, metrik, dan confusion matrix pada data uji.

### Clustering pelanggan

- **Fitur awal.** `tenure`, `MonthlyCharges`, dan `TotalCharges`. Gunakan versi data dan preprocessing yang sama, termasuk scaling. Gunakan label `Churn` historis setelah klaster terbentuk untuk membaca profil setiap segmen.
- **Kandidat.** K-Means, Agglomerative Clustering, dan DBSCAN.
- **Eksperimen.** Variasikan jumlah klaster untuk K-Means dan Agglomerative. Catat inertia untuk membaca elbow K-Means. Untuk DBSCAN, variasikan `eps` dan `min_samples`, lalu laporkan jumlah dan persentase titik noise.
- **Usulan pemilihan.** Laporkan silhouette, Davies–Bouldin, dan Calinski–Harabasz saat ada minimal dua klaster dengan jumlah klaster di bawah jumlah baris yang dinilai. Untuk DBSCAN, hitung metrik pada baris yang mendapat klaster dan sertakan cakupan datanya karena skor itu dihitung pada subset. Bandingkan juga ukuran, profil, dan keterbacaan segmen. Sebelum memilih model untuk dashboard, verifikasi cara menghasilkan label pada versi dataset yang akan diproses Backend.

### Regresi tagihan bulanan

- **Target.** `MonthlyCharges`. Keluarkan `MonthlyCharges`, `TotalCharges`, `Churn`, dan `customerID` dari fitur.
- **Kandidat.** Dummy Regressor sebagai baseline minimum, Linear Regression, Ridge atau Lasso, Decision Tree Regressor, dan Random Forest Regressor.
- **Eksperimen.** Uji tingkat regularisasi serta kedalaman pohon yang relevan pada data latih. Pakai fitur dan fold yang sama untuk seluruh kandidat regresi.
- **Usulan pemilihan.** Gunakan MAE sebagai pembanding utama karena dapat dibaca dalam satuan biaya dataset. Laporkan juga RMSE dan R², lalu sertakan grafik aktual versus prediksi dan residual pada evaluasi akhir.

### Format hasil eksperimen

Buat satu tabel per tugas dengan kolom kandidat, konfigurasi, metrik, dan catatan. Pada klasifikasi dan regresi, cantumkan skor CV tiap kandidat dan hasil uji model terpilih secara terpisah. Pada clustering, tambahkan jumlah klaster, cakupan, dan ringkasan profil segmen. Catat alasan pemilihan model serta versi dataset dan artefak yang dipakai pada dashboard.

Pasang Jupyter sesuai kebutuhan untuk menjalankan notebook. Folder data mentah dan hasil eksperimen diabaikan Git.

Metrik internal klaster dan penjelasan kesalahan regresi pada metadata dihitung dari model yang baru dilatih. Metadata klasifikasi mencatat kelas angka model melalui `model_positive_class`, sedangkan `positive_class` menyatakan makna churn sebagai `Yes`. Contoh rekomendasi memakai probabilitas sebelum pembulatan agar cocok dengan inference Backend.

## Hasil serah terima

- File churn berversi untuk dipasang Backend, kamus data, notebook EDA, serta skrip cleaning, training, dan evaluasi yang dapat dijalankan ulang.
- Metrik dan grafik eksperimen, termasuk perbandingan dengan baseline dan alasan pemilihan model akhir.
- Pipeline terpilih lengkap dengan preprocessing, daftar dan tipe fitur, versi artefak dan dependensi, threshold churn, serta contoh input dan output dari dataset acuan.
- Pemetaan ID ke nama segmen, profil setiap segmen, dan aturan retensi yang dapat diterapkan oleh Backend.
