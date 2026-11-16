# Usulan kontrak integrasi

RetenSight menggunakan satu file churn pelanggan yang dipasang di server. Backend memproses file otomatis saat dataset dan model pertama kali tersedia atau ketika salah satu versinya berubah. Backend menyimpan hasil beserta kedua versi agar Frontend dapat membaca hasil untuk versi aktif melalui endpoint berikut.

| Metode dan path | Tujuan | Status implementasi |
| --- | --- | --- |
| `GET /api/health` | Memeriksa ketersediaan layanan | Tersedia |
| `GET /api/dataset-summary` | Menyediakan status pemrosesan, identitas dataset, dan ringkasan eksplorasi | Tersedia |
| `GET /api/predictions` | Menyediakan hasil analisis tersimpan per pelanggan | Tersedia |
| `GET /api/model-info` | Menampilkan versi model, fitur, threshold, dan profil segmen | Tersedia |
| `GET /api/evaluations` | Menampilkan hasil evaluasi eksperimen yang tersimpan | Usulan |

## Frontend dan Backend

Ringkasan memuat nama dataset, versi dataset dan model, status pemrosesan, jumlah pelanggan, serta distribusi yang disepakati untuk grafik. Jika kolom `Churn` tersedia, gunakan label historis untuk ringkasan churn aktual. Versi dataset dan model pada respons membantu Frontend mencocokkan ringkasan dengan hasil per pelanggan.

Respons untuk ringkasan, prediksi pelanggan, dan metadata model memakai struktur yang sama dengan fixture demo.

| Field | Isi usulan |
| --- | --- |
| `is_demo` | Boolean yang bernilai `true` untuk fixture dan `false` untuk API |
| `status` | `preparing` saat analisis berjalan, `ready` saat hasil untuk versi aktif siap, atau `failed` saat pemrosesan gagal |
| `dataset_version`, `model_version` | String versi pasangan yang diproses. Gunakan `null` jika versi belum diketahui |
| `data` | Objek ringkasan, hasil per pelanggan, atau metadata model sesuai endpoint saat `ready`. Gunakan `null` saat hasil belum tersedia |
| `error` | Objek dengan `code` dan `message` saat `failed`. Dapat memuat `row` dan `field` untuk masalah CSV, atau `model_release` jika manifest terbaca tetapi fingerprint paket belum bisa dihitung. Bernilai `null` untuk kondisi lain |

Gunakan `GET /api/dataset-summary` untuk memeriksa kesiapan hasil. HTTP 200 pada ketiga endpoint baca berarti status batch bisa dibaca. Saat `preparing` atau `failed`, `data` bernilai `null`. Ringkasan menyertakan `dataset_name` pada semua status. Saat `ready`, objek `data` memuat `processed_rows`, churn historis (`actual_churn`), serta distribusi untuk grafik kontrak, tenure, dan tagihan. `actual_churn.rate` berada di skala 0–1 dan dihitung dari jumlah label `Yes` dibagi jumlah label aktual `Yes` dan `No`. Gunakan `null` untuk `actual_churn` jika label historis tidak tersedia.

Frontend menggabungkan respons jika `dataset_version` dan `model_version` cocok. Versi dapat berubah di antara dua request saat batch baru dimulai. Ketiga endpoint menyediakan header `Cache-Control: no-store` agar browser membaca status terkini. API mengizinkan origin lokal `http://localhost:3000` dan `http://127.0.0.1:3000`.

| Field per pelanggan | Tipe usulan |
| --- | --- |
| `customer_id` | String |
| `churn_probability` | Angka antara 0 dan 1 |
| `churn_prediction` | Label `Yes` atau `No` |
| `segment_id` | Integer |
| `segment_name` | String |
| `predicted_monthly_charges` | Angka |
| `recommendation` | String |

Kirim hasil per pelanggan sebagai `data.predictions`. Pertahankan `customerID` sebagai `customer_id` agar hasil dapat dicocokkan dengan pelanggan asal. Sertakan `data.processed_rows` dan `data.warnings`. Gunakan satuan biaya dataset untuk estimasi tagihan dan beri label simulasi pada rekomendasi retensi. Metadata model memuat algoritma dan fitur per model, kelas positif dan threshold churn, pemetaan dan profil segmen, serta target dan satuan regresi. Profil segmen menyertakan `customer_count`, `average_tenure_months` pada dataset aktif, dan `is_noise`. Untuk evaluasi model, tampilkan metrik dan grafik dari eksperimen yang diserahkan Data. Jika hasil per pelanggan mencakup baris latih, gunakan hasil tersebut untuk eksplorasi dan cantumkan sumber data uji pada evaluasi.

### Cara memakai fixture

Ambil objek berikut dari [`backend/fixtures/dashboard.demo.json`](../backend/fixtures/dashboard.demo.json) sebagai body respons mock.

| Kondisi | Endpoint | Objek JSON |
| --- | --- | --- |
| Hasil siap | `GET /api/dataset-summary` | `ready.dataset_summary` |
| Hasil siap | `GET /api/predictions` | `ready.predictions` |
| Hasil siap | `GET /api/model-info` | `ready.model_info` |
| Sedang diproses | `GET /api/dataset-summary` | `preparing.dataset_summary` |
| Gagal diproses | `GET /api/dataset-summary` | `failed.dataset_summary` |

Frontend dapat memakai ringkasan untuk menentukan tampilan status, lalu membaca prediksi dan metadata dari pasangan versi yang sama saat hasil siap. File fixture berisi nilai sintetis dan parameter model demo. Payload evaluasi akan menggunakan hasil eksperimen dari Data.

## Data dan Backend

### Lokasi dan versi

- Gunakan `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` sebagai usulan lokasi file lokal dari root repo. Backend membaca file yang sudah ditempatkan tim di komputer yang menjalankan FastAPI.
- `dataset_version` berupa `sha256:<hash>` dari isi CSV yang diproses. Nilai ini bisa dicocokkan dengan hash file pada serah terima Data. Letakkan paket model dan `manifest.json` di `backend/artifacts/`.
- Data memberi nama rilis pada `model_version` di manifest. Backend menambahkan fingerprint isi manifest dan ketiga artefak untuk mendapatkan versi yang disajikan, misalnya `model-v1@sha256:<hash>`.
- Gunakan kedua versi saat menyimpan dan menyajikan hasil. Perubahan pada salah satu versi memicu pemrosesan ulang file sesuai desain aplikasi.
- Tim Data menyerahkan file berversi, pipeline lengkap dengan preprocessing, daftar fitur dan tipe input, versi dependensi, threshold churn, profil dan pemetaan ID segmen, aturan retensi, hasil evaluasi, serta contoh hasil per pelanggan. Training dilakukan offline.

### Draf skema CSV

Pembacaan memakai CSV UTF-8 dengan pemisah koma, header dengan nama kolom sesuai sumber, dan titik sebagai pemisah desimal. Kolom wajib mencakup `customerID`, `tenure`, `Contract`, dan `MonthlyCharges` untuk ringkasan, serta fitur yang dinyatakan oleh setiap pipeline. Cocokkan tabel ini dengan file acuan dan daftar fitur tiap pipeline yang diserahkan Data.

| Kolom | Tipe dan arti |
| --- | --- |
| `customerID` | Teks unik dan terisi. Pertahankan nol di awal |
| `tenure` | Bilangan bulat nonnegatif dalam bulan |
| `MonthlyCharges` | Angka desimal nonnegatif dalam satuan biaya dataset |
| `TotalCharges` | Angka desimal nonnegatif dalam satuan biaya dataset. Sel kosong atau hanya spasi dibaca sebagai nilai hilang sesuai kebijakan pipeline |
| `SeniorCitizen` | Bilangan bulat `0` atau `1` |
| `gender`, `Partner`, `Dependents`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod` | Teks kategorikal. Data mencatat kategori yang dikenali pipeline, termasuk nilai khusus seperti `No internet service` dan `No phone service` |
| `Churn` | Label historis `Yes` atau `No`. Digunakan sebagai target saat training dan untuk ringkasan aktual jika tersedia |

Kolom `customerID` dikeluarkan dari semua fitur. Klasifikasi menggunakan `Churn` sebagai target. Clustering memakai `tenure`, `MonthlyCharges`, dan `TotalCharges` sebagai fitur awal. Regresi memprediksi `MonthlyCharges` dan mengecualikan `TotalCharges` serta `Churn` dari fitur.

### Contoh pembacaan dan penanganan nilai invalid

Cuplikan sintetis ini memakai sebagian kolom untuk memperjelas aturan baca.

```csv
customerID,tenure,Contract,MonthlyCharges,TotalCharges,Churn
00123,12,Month-to-month,49.90,598.80,Yes
00456,0,One year,19.85," ",No
00789,abc,Two year,29.00,174.00,No
```

1. Baris 2 menghasilkan ID teks `00123`, tenure `12` bulan, dan tagihan `49.90`. Kedua role menggunakan ID utuh saat mencocokkan hasil.
2. Baris 3 memiliki `TotalCharges` yang hanya berisi spasi. Perlakukan sebagai nilai hilang. Data perlu mengonfirmasi bahwa pipeline menanganinya sebelum batch menerima baris tersebut.
3. Baris 4 berisi `abc` pada kolom bilangan bulat. Batch berhenti dengan status `failed` dan menampilkan kode `INVALID_FIELD`, nomor baris, nama kolom, dan pesan yang bisa diperbaiki tim. Kolom wajib yang hilang atau ID duplikat juga menghentikan batch.

Skenario fixture `ready` memakai dua baris pertama setelah header sebagai contoh. Skenario `failed` menunjukkan respons jika baris dengan tenure invalid ikut diproses.

### Paket model dari Data

Manifest menyimpan petunjuk untuk menjalankan tiga pipeline yang sudah dilatih. Contoh berikut menunjukkan format serah terima. Ganti nama artefak, versi, fitur, kelas positif, threshold, segmen, dan aturan sesuai hasil eksperimen.

```json
{
  "model_version": "model-v1",
  "dependencies": {
    "joblib": "1.4.2",
    "numpy": "2.2.6",
    "pandas": "2.2.3",
    "scikit-learn": "1.6.1"
  },
  "allow_missing_total_charges": true,
  "categories": {
    "Contract": ["Month-to-month", "One year", "Two year"]
  },
  "classification": {
    "artifact": "churn.joblib",
    "algorithm": "Logistic Regression",
    "features": ["tenure", "Contract", "MonthlyCharges"],
    "positive_class": "Yes",
    "threshold": 0.5
  },
  "clustering": {
    "artifact": "segments.joblib",
    "algorithm": "K-Means",
    "features": ["tenure", "MonthlyCharges", "TotalCharges"],
    "segments": [
      {"segment_id": 0, "segment_name": "Pelanggan baru", "profile": "Masa berlangganan pendek."},
      {"segment_id": 1, "segment_name": "Masa langganan lebih panjang"}
    ]
  },
  "regression": {
    "artifact": "charges.joblib",
    "algorithm": "Ridge",
    "features": ["tenure", "Contract"],
    "target": "MonthlyCharges",
    "unit": "satuan biaya dataset"
  },
  "retention_rules": [
    {
      "churn_prediction": "Yes",
      "min_probability": 0.6,
      "segment_ids": [1],
      "recommendation": "Tawarkan peninjauan kontrak."
    }
  ],
  "fallback_recommendation": "Pantau pengalaman pelanggan."
}
```

- Simpan file `.joblib` atau `.pkl` bersama manifest. Gunakan hasil ekspor dari tim Data. Cocokkan nama dan urutan fitur dengan input pipeline saat training.
- Gunakan `predict_proba()` dan `classes_` untuk klasifikasi biner. Isi `positive_class` dengan nilai kelas yang berarti churn di model, misalnya `"Yes"` atau `1`. Pipeline segmentasi dan regresi menyediakan `predict()`. Ketiga pipeline mengembalikan satu hasil untuk setiap baris input dengan urutan yang sama.
- Daftarkan semua ID segmen yang bisa dihasilkan model. Jika ada titik noise, tentukan `noise_label` dan sertakan ID tersebut di `segments` dengan nama tampilan.
- Aktifkan `allow_missing_total_charges` saat pipeline yang mengonsumsi fitur tersebut menangani nilai hilang. Tambahkan kolom ke `categories` jika paket hanya menerima daftar kategori tertentu pada kolom itu.
- Untuk simulasi retensi, jalankan aturan sesuai urutannya. Semua kondisi dalam satu aturan harus terpenuhi. Batas `min_probability` dan `max_probability` inklusif. Gunakan `fallback_recommendation` ketika hasil model valid dan semua aturan tidak cocok. Hasil model yang hilang atau invalid membuat batch berstatus `failed`.
- Cantumkan versi `joblib`, `numpy`, `pandas`, dan `scikit-learn` saat ekspor. Sertakan dependensi tambahan yang diperlukan paket agar Backend dapat memeriksa versinya.
