# RetenSight

Scaffold dashboard analitik untuk file churn pelanggan telekomunikasi yang disiapkan tim. Dataset acuan adalah IBM Telco Customer Churn. Dashboard menampilkan eksplorasi data, prediksi churn, segmentasi pelanggan, estimasi tagihan bulanan, dan evaluasi model.

## Alur aplikasi

1. Tim Data memeriksa dataset, melatih dan mengevaluasi model secara offline, lalu menyerahkan versi sumber dataset, pipeline, dan metadata ke Backend.
2. Backend memproses file otomatis saat dataset dan model pertama kali tersedia, lalu setiap kali salah satu versinya berubah. Hasil analisis disimpan dengan kedua versi tersebut agar bisa digunakan kembali.
3. Frontend mengambil ringkasan dan hasil tersimpan melalui API saat pengguna membuka dashboard. Jika hasil sedang disiapkan, tampilkan status proses dan perbarui tampilan setelah hasil siap.

| Halaman | Isi |
| --- | --- |
| Beranda | Nama dan versi dataset, jumlah pelanggan yang dianalisis, ringkasan churn aktual jika label tersedia, dan status kesiapan hasil |
| Eksplorasi | Distribusi kontrak, masa berlangganan, tagihan, dan churn historis dari dataset |
| Prediksi & Segmen | Probabilitas dan label prediksi churn, segmen, estimasi tagihan, dan simulasi rekomendasi per pelanggan |
| Evaluasi Model | Perbandingan algoritma, metrik, dan grafik eksperimen dari tim Data |

| Folder | Stack | Isi awal |
| --- | --- | --- |
| `frontend/` | Next.js, TypeScript, Tailwind CSS | Halaman awal dan konfigurasi build |
| `backend/` | Python, FastAPI, Uvicorn | Pemrosesan dataset, hasil tersimpan, dan lima endpoint dashboard |
| `data/` | Python, pandas, NumPy, scikit-learn, joblib | Dependensi dan panduan kerja Data |
| `docs/` | Markdown | Usulan kontrak integrasi |

## Menjalankan scaffold

Gunakan Node.js 20.9 atau lebih baru dan Python 3.11 atau 3.12. Jalankan perintah dari root repo pada terminal terpisah.

**Frontend**

```powershell
cd frontend
npm ci
npm run dev
```

Buka [halaman awal](http://localhost:3000). Jalankan `npm run check` untuk pengecekan TypeScript dan `npm run build` untuk build produksi. Script Next.js memakai Webpack karena Turbopack gagal memulai PostCSS pada mesin inisialisasi.

**Backend**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Buka [health check](http://127.0.0.1:8000/api/health) dan pastikan responsnya `{"status":"ok"}`. [Swagger UI](http://127.0.0.1:8000/docs) menampilkan endpoint yang tersedia. Untuk pengembangan tes, pasang `backend/requirements-dev.txt`.

**Data dan Machine Learning**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r data/requirements.txt
```

Jika `.venv` sudah dibuat untuk Backend, gunakan lingkungan yang sama atau buat lingkungan terpisah. Lihat [panduan tim Data](data/README.md) untuk dataset dan hasil yang perlu diserahkan ke Backend.

## Memulai kerja tim

Gunakan branch per fitur dan PR. Sepakati [kontrak API dan artefak](docs/api.md) sebelum integrasi pertama.

| Role | Pekerjaan pertama | Serah terima |
| --- | --- | --- |
| Frontend | Buat Beranda dengan ringkasan dataset dan status hasil. Pakai mock berlabel demo untuk menyiapkan tampilan sebelum API tersedia. | Dashboard responsif, grafik, hasil per pelanggan, dan integrasi API. [Panduan Frontend](frontend/README.md) |
| Backend | Siapkan pembacaan file di server, validasi dataset, dan respons demo untuk endpoint ringkasan. | Pemrosesan otomatis per versi, penyimpanan hasil, API terdokumentasi, dan pengujian. [Panduan Backend](backend/README.md) |
| Data | Verifikasi file churn, buat EDA dan kamus data, lalu bangun baseline klasifikasi, clustering, dan regresi. | Dataset berversi, pipeline, versi dependensi, profil segmen, aturan retensi, dan metrik eksperimen. [Panduan Data](data/README.md) |

Target integrasi pertama adalah dashboard yang membaca ringkasan dan hasil model dari satu versi dataset yang dipasang di server. Periksa kecocokan hasil dengan `customerID`, waktu pemrosesan batch, dan waktu respons dashboard saat membaca hasil tersimpan.

Backend sudah diverifikasi dengan paket model dari skrip Data. Cara memasang artefak dan menjalankan verifikasi tersedia di [panduan Backend](backend/README.md), dengan hasil pemeriksaan pada [catatan serah terima](docs/backend-handover.md).

Untuk lingkup awal, gunakan satu dataset publik, training offline, dan rekomendasi retensi berbasis aturan sebagai simulasi pada dataset historis. Akun, integrasi billing atau CRM, dan kampanye otomatis berada di luar lingkup awal.
