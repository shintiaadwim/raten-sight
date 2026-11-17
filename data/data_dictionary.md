# Kamus Data & Skema Fitur RetenSight (Role Data)

Dokumen ini memenuhi checklist **Tugas Pertama — Verifikasi dataset dan bagikan skema** pada [docs/jobdesk.md](../docs/jobdesk.md#L9-L15).

---

## 1. Identitas & Verifikasi Dataset Acuan

| Atribut | Detail |
| --- | --- |
| **Lokasi File Acuan** | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` |
| **Sumber Dataset** | [IBM Telco Customer Churn (Kaggle - blastchar/telco-customer-churn)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) |
| **Versi Dataset** | `telco-churn-v1.0` |
| **Jumlah Baris Awal** | `7.043` baris |
| **Jumlah Kolom** | `21` kolom |
| **Jumlah Baris Sesudah Cleaning** | `7.043` baris *(tidak ada baris yang dihapus)* |
| **Satuan Biaya Dataset** | `USD` (`$`) |

### Ringkasan Pemeriksaan Kualitas Data
1. **Validasi `customerID`:**
   - Nilai kosong (`null` / string kosong): **0 baris**
   - Nilai duplikat: **0 baris** (seluruh **7.043** `customerID` bersifat unik).
2. **Distribusi Target `Churn` (Penyebut = 7.043 pelanggan):**
   - `No` (Pelanggan bertahan): **5.174 pelanggan (73,46%)**
   - `Yes` (Pelanggan churn / kelas positif): **1.869 pelanggan (26,54%)**
3. **Nilai Kosong pada `TotalCharges` & Keputusan Cleaning:**
   - Pada file CSV mentah, kolom `TotalCharges` terbaca sebagai `object` (string) karena terdapat **11 baris berisi spasi `" "`**.
   - Ketika dikonversi ke numerik menggunakan `pd.to_numeric(df['TotalCharges'], errors='coerce')`, muncul **11 nilai `NaN`**.
   - Ke-11 baris tersebut seluruhnya merupakan pelanggan baru dengan **`tenure == 0` bulan** dan **`Churn == 'No'`** (`4472-LVYGI`, `3115-CZMZD`, `5709-LVOEQ`, `4367-NUYAO`, `1371-DWPAZ`, `7644-OMVMY`, `3213-VVOLG`, `2520-SGTTA`, `2923-ARZLG`, `4075-WKNIU`, `2775-SEFEE`).
   - **Keputusan Cleaning:**
     - Saat tahap baca CSV: konversi `TotalCharges` ke `float64` dengan `pd.to_numeric(..., errors='coerce')`.
     - Nilai `NaN` pada `TotalCharges` diisi dengan **`0.0`** (karena pelanggan dengan masa berlangganan `0` bulan belum memiliki akumulasi tagihan total), serta dilengkapi `SimpleImputer` di dalam pipeline scikit-learn agar ketika model dijalankan di produksi pada input serupa, tidak ada baris yang gagal diproses.
     - Jumlah baris **sebelum cleaning = 7.043** dan **sesudah cleaning = 7.043**.
4. **Perlakuan Kategori Khusus (`No internet service` & `No phone service`):**
   - Kategori `No internet service` (pada 6 kolom layanan internet tambahan) dan `No phone service` (pada kolom `MultipleLines`) dipertahankan apa adanya sebagai kategori valid yang merepresentasikan ketiadaan layanan induk, lalu di-encode menggunakan `OneHotEncoder(handle_unknown='ignore')` di dalam pipeline agar aman terhadap kategori baru yang belum pernah muncul saat `fit`.

---

## 2. Kamus Data (21 Kolom)

| No | Nama Kolom | Arti / Deskripsi | Tipe Data (Setelah Cleaning) | Kategori / Rentang Nilai | Unit | Contoh Nilai | Peran Kolom |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `customerID` | ID unik setiap pelanggan | `string` | 7.043 kode unik (format `XXXX-XXXXX`) | — | `"7590-VHVEG"` | **Identitas** (Bukan fitur) |
| 2 | `gender` | Jenis kelamin pelanggan | `string` (kategorikal) | `Female`, `Male` | — | `"Female"` | Fitur (Klasifikasi, Regresi) |
| 3 | `SeniorCitizen` | Status lansia (1 = Ya, 0 = Tidak) | `int64` (biner) | `0`, `1` | — | `0` | Fitur (Klasifikasi, Regresi) |
| 4 | `Partner` | Apakah pelanggan memiliki pasangan | `string` (kategorikal) | `Yes`, `No` | — | `"Yes"` | Fitur (Klasifikasi, Regresi) |
| 5 | `Dependents` | Apakah pelanggan memiliki tanggungan | `string` (kategorikal) | `No`, `Yes` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 6 | `tenure` | Lama berlangganan pelanggan | `int64` (numerik) | `0` – `72` (rata-rata: `32,37`) | Bulan | `1` | Fitur (Klasifikasi, Clustering, Regresi) |
| 7 | `PhoneService` | Apakah berlangganan layanan telepon | `string` (kategorikal) | `No`, `Yes` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 8 | `MultipleLines` | Apakah memiliki lebih dari satu saluran telepon | `string` (kategorikal) | `No phone service`, `No`, `Yes` | — | `"No phone service"` | Fitur (Klasifikasi, Regresi) |
| 9 | `InternetService` | Jenis penyedia layanan internet | `string` (kategorikal) | `DSL`, `Fiber optic`, `No` | — | `"DSL"` | Fitur (Klasifikasi, Regresi) |
| 10 | `OnlineSecurity` | Layanan keamanan online tambahan | `string` (kategorikal) | `No`, `Yes`, `No internet service` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 11 | `OnlineBackup` | Layanan pencadangan online tambahan | `string` (kategorikal) | `Yes`, `No`, `No internet service` | — | `"Yes"` | Fitur (Klasifikasi, Regresi) |
| 12 | `DeviceProtection` | Layanan perlindungan perangkat tambahan | `string` (kategorikal) | `No`, `Yes`, `No internet service` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 13 | `TechSupport` | Layanan dukungan teknis tambahan | `string` (kategorikal) | `No`, `Yes`, `No internet service` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 14 | `StreamingTV` | Layanan streaming TV | `string` (kategorikal) | `No`, `Yes`, `No internet service` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 15 | `StreamingMovies` | Layanan streaming film | `string` (kategorikal) | `No`, `Yes`, `No internet service` | — | `"No"` | Fitur (Klasifikasi, Regresi) |
| 16 | `Contract` | Jenis durasi kontrak berlangganan | `string` (kategorikal) | `Month-to-month`, `One year`, `Two year` | — | `"Month-to-month"` | Fitur (Klasifikasi, Regresi) |
| 17 | `PaperlessBilling` | Apakah menggunakan tagihan tanpa kertas (elektronik) | `string` (kategorikal) | `Yes`, `No` | — | `"Yes"` | Fitur (Klasifikasi, Regresi) |
| 18 | `PaymentMethod` | Metode pembayaran tagihan pelanggan | `string` (kategorikal) | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` | — | `"Electronic check"` | Fitur (Klasifikasi, Regresi) |
| 19 | `MonthlyCharges` | Tagihan bulanan yang dikenakan saat ini | `float64` (numerik) | `18.25` – `118.75` (rata-rata: `64.76`) | USD (`$`) | `29.85` | **Target Regresi** & Fitur (Klasifikasi, Clustering) |
| 20 | `TotalCharges` | Total akumulasi tagihan selama berlangganan | `float64` (numerik, konversi dari string) | `0.00` – `8684.80` (rata-rata: `2279.73` setelah isi `0.0`) | USD (`$`) | `29.85` | Fitur (Klasifikasi, Clustering) |
| 21 | `Churn` | Apakah pelanggan berhenti berlangganan bulan lalu | `string` (kategorikal biner) | `No` (73,46%), `Yes` (26,54%) | — | `"No"` | **Target Klasifikasi** (`Yes` = kelas positif `1`) |

---

## 3. Daftar Fitur dan Tipe Input per Model

Kolom **`customerID` selalu dikeluarkan dari fitur ketiga model**, tetapi wajib dipertahankan pada tabel utama untuk mencocokkan dan menggabungkan hasil prediksi per pelanggan.

### A. Model 1 — Klasifikasi Churn (`Churn` = Target, Kelas Positif = `"Yes"`)
- **Jumlah Fitur Input:** **19 kolom** (keluarkan `customerID` dan `Churn`)
- **Fitur Numerik (4 kolom):**
  - `SeniorCitizen` (`int64`), `tenure` (`int64`), `MonthlyCharges` (`float64`), `TotalCharges` (`float64`)
- **Fitur Kategorikal (15 kolom):**
  - `gender`, `Partner`, `Dependents`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod` (seluruhnya `string`)

### B. Model 2 — Clustering Pelanggan (Unsupervised)
- **Jumlah Fitur Input:** **3 kolom numerik**
- **Daftar Fitur:**
  1. `tenure` (`int64` / `float64`)
  2. `MonthlyCharges` (`float64`)
  3. `TotalCharges` (`float64`)
- **Catatan:** Kolom `Churn` **tidak** dimasukkan saat pembentukan klaster (`fit`), melainkan hanya digunakan setelah klaster terbentuk untuk membaca profil proporsi churn historis tiap segmen.

### C. Model 3 — Regresi Tagihan Bulanan (`MonthlyCharges` = Target)
- **Jumlah Fitur Input:** **17 kolom** (keluarkan `customerID`, `Churn`, `MonthlyCharges`, dan `TotalCharges`)
- **Fitur Numerik (2 kolom):**
  - `SeniorCitizen` (`int64`), `tenure` (`int64`)
- **Fitur Kategorikal (15 kolom):**
  - `gender`, `Partner`, `Dependents`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`

---

## 4. Satu Baris Contoh Acuan & Cara Mencocokkan Hasil (`customerID`)

### Baris Contoh ke-1 (Indeks 0 dari `WA_Fn-UseC_-Telco-Customer-Churn.csv`)
```json
{
  "customerID": "7590-VHVEG",
  "gender": "Female",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 1,
  "PhoneService": "No",
  "MultipleLines": "No phone service",
  "InternetService": "DSL",
  "OnlineSecurity": "No",
  "OnlineBackup": "Yes",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "No",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 29.85,
  "TotalCharges": 29.85,
  "Churn": "No"
}
```

### Cara Mencocokkan Hasil Melalui `customerID`
1. Simpan kolom `df["customerID"]` dengan urutan indeks baris yang sama sebelum memisahkan matriks fitur tiap model (`X_clf`, `X_cluster`, `X_reg`).
2. Jalankan ketiga pipeline pada subset kolom masing-masing.
3. Satukan kembali hasil prediksi berdasarkan indeks / `customerID` yang bersesuaian:
   - `customer_id`: nilai dari `df["customerID"]` (contoh: `"7590-VHVEG"`)
   - `churn_probability` & `churn_prediction`: keluaran Model Klasifikasi
   - `segment_id` & `segment_name`: keluaran Model Clustering
   - `predicted_monthly_charges`: keluaran Model Regresi (dalam satuan USD `$`)
   - `recommendation`: hasil evaluasi aturan simulasi retensi berdasarkan `churn_prediction`/`churn_probability` dan `segment_id`.

---

## 5. Definisi Ringkasan untuk Grafik Eksplorasi

Seluruh proporsi/persentase pada eksplorasi dihitung menggunakan **penyebut total pelanggan `N = 7.043`** (atau jumlah pelanggan dalam kategori terkait bila merupakan *churn rate per kategori*):

1. **Ringkasan Churn Aktual:**
   - Jumlah dan persentase pelanggan `Churn = Yes` (`1.869` / `26,54%`) vs `Churn = No` (`5.174` / `73,46%`), dengan penyebut `7.043`.
2. **Distribusi Kontrak (`Contract`):**
   - Jumlah pelanggan dan proporsi churn (`Yes` vs `No`) pada setiap tipe kontrak: `Month-to-month`, `One year`, dan `Two year`.
3. **Distribusi Masa Berlangganan (`tenure`):**
   - Histogram / pengelompokan masa berlangganan dalam satuan **bulan** (`0–12 bulan`, `13–24 bulan`, `25–48 bulan`, `49–72 bulan`) beserta perbandingan antara pelanggan bertahan (`No`) dan berhenti (`Yes`).
4. **Distribusi Tagihan (`MonthlyCharges` & `TotalCharges`):**
   - Distribusi nilai tagihan dalam satuan **USD (`$`)** serta perbandingan rata-rata/median tagihan bulanan antara kelompok `Churn = Yes` dan `Churn = No`.
5. **Distribusi Layanan (`InternetService` & Layanan Tambahan):**
   - Jumlah pelanggan dan tingkat churn berdasarkan jenis internet (`DSL`, `Fiber optic`, `No`) serta kepemilikan layanan tambahan (`OnlineSecurity`, `TechSupport`, dll.).
