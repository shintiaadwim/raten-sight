# Usulan kontrak integrasi

RetenSight menggunakan satu file churn pelanggan yang dipasang di server. Backend memproses file otomatis saat dataset dan model pertama kali tersedia atau ketika salah satu versinya berubah. Backend menyimpan hasil beserta kedua versi agar Frontend dapat membaca hasil untuk versi aktif melalui endpoint berikut.

| Metode dan path | Tujuan | Status scaffold |
| --- | --- | --- |
| `GET /api/health` | Memeriksa ketersediaan layanan | Tersedia |
| `GET /api/dataset-summary` | Menyediakan status pemrosesan, identitas dataset, dan ringkasan eksplorasi | Usulan |
| `GET /api/predictions` | Menyediakan hasil analisis tersimpan per pelanggan | Usulan |
| `GET /api/model-info` | Menampilkan versi model, fitur, threshold, dan profil segmen | Usulan |
| `GET /api/evaluations` | Menampilkan hasil evaluasi eksperimen yang tersimpan | Usulan |

## Frontend dan Backend

Ringkasan memuat nama dataset, versi dataset dan model, status pemrosesan, jumlah pelanggan, serta distribusi yang disepakati untuk grafik. Jika kolom `Churn` tersedia, gunakan label historis untuk ringkasan churn aktual. Versi dataset dan model pada respons membantu Frontend mencocokkan ringkasan dengan hasil per pelanggan.

Usulan status pemrosesan adalah `preparing` saat analisis dijalankan, `ready` saat hasil untuk versi aktif tersedia, dan `failed` jika file atau artefak tidak dapat diproses. Sertakan pesan untuk status gagal dan label demo jika menggunakan fixture.

| Field per pelanggan | Tipe usulan |
| --- | --- |
| `customer_id` | String |
| `churn_probability` | Angka antara 0 dan 1 |
| `churn_prediction` | Label `Yes` atau `No` |
| `segment_id` | Integer |
| `segment_name` | String |
| `predicted_monthly_charges` | Angka |
| `recommendation` | String |

Pertahankan `customerID` untuk mencocokkan hasil dengan pelanggan asal. Sertakan jumlah baris yang diproses dan peringatan jika ada. Gunakan satuan biaya dataset untuk estimasi tagihan dan beri label simulasi pada rekomendasi retensi. Untuk evaluasi model, tampilkan metrik dan grafik dari eksperimen yang diserahkan Data. Jika hasil per pelanggan mencakup baris latih, gunakan hasil tersebut untuk eksplorasi dan cantumkan sumber data uji pada evaluasi.

## Data dan Backend

Sepakati lokasi file di server, skema fitur per model, dan format versi dataset serta artefak. Tim Data menyerahkan file churn berversi, pipeline lengkap dengan preprocessing, daftar fitur dan tipe input, versi dependensi, threshold churn, profil dan pemetaan ID segmen, aturan retensi, hasil evaluasi, serta contoh hasil per pelanggan. Backend memvalidasi file dan memprosesnya dengan pipeline terlatih. Training dilakukan offline.

Kolom `customerID` dikeluarkan dari semua fitur. Klasifikasi menggunakan `Churn` sebagai target. Clustering memakai `tenure`, `MonthlyCharges`, dan `TotalCharges` sebagai fitur awal. Regresi memprediksi `MonthlyCharges` dan mengecualikan `TotalCharges` serta `Churn` dari fitur.
