# Usulan kontrak integrasi

Tim perlu menyepakati kolom wajib dan opsional, batas ukuran dan jumlah baris, format error, dan perilaku saat sebagian input invalid sebelum mengandalkan kontrak ini.

| Metode dan path | Tujuan | Status scaffold |
| --- | --- | --- |
| `GET /api/health` | Memeriksa ketersediaan layanan | Tersedia |
| `POST /api/predictions` | Menerima CSV dan mengembalikan analisis | Usulan |
| `GET /api/model-info` | Menampilkan versi model, fitur, threshold, dan profil segmen | Usulan |
| `GET /api/evaluations` | Menampilkan hasil evaluasi eksperimen yang tersimpan | Usulan |

## Frontend dan Backend

Usulan unggahan adalah CSV UTF-8 melalui `multipart/form-data` dengan field `file`. Pertahankan `customerID` untuk mencocokkan baris. `Churn` opsional karena pelanggan yang sedang diprediksi dapat belum memiliki label. Gunakan satuan biaya dataset pada tampilan.

| Field per pelanggan | Tipe usulan |
| --- | --- |
| `customer_id` | String |
| `churn_probability` | Angka antara 0 dan 1 |
| `churn_prediction` | Label `Yes` atau `No` |
| `segment_id` | Integer |
| `segment_name` | String |
| `predicted_monthly_charges` | Angka |
| `recommendation` | String |

Sertakan jumlah baris diproses, versi model, dan peringatan di metadata respons. Tandai mock dan respons sementara sebagai demo. Usulan untuk input parsial adalah menyediakan estimasi tagihan jika fitur regresinya lengkap, lalu memberi peringatan dan mengembalikan `null` pada hasil model yang kekurangan fitur. Sepakati juga apakah satu baris invalid menolak seluruh file.

## Data dan Backend

Sepakati nama, format, dan versi artefak sebelum ekspor. Tim Data menyerahkan fitted pipeline lengkap dengan preprocessing, daftar fitur dan tipe input, versi dependensi, threshold churn, profil dan pemetaan ID segmen, aturan retensi, hasil evaluasi, serta contoh input-output. Backend memuat pipeline dan melakukan inference. Training dilakukan offline.

Kolom `customerID` dikeluarkan dari semua fitur. Klasifikasi menggunakan `Churn` sebagai target. Clustering memakai `tenure`, `MonthlyCharges`, dan `TotalCharges` sebagai fitur awal. Regresi memprediksi `MonthlyCharges` dan mengecualikan `TotalCharges` serta `Churn` dari fitur.
