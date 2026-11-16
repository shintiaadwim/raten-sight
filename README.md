# RetenSight

Scaffold proyek analitik pelanggan telekomunikasi. Tim akan mengembangkan prediksi churn, segmentasi pelanggan, dan estimasi tagihan bulanan.

| Folder | Stack | Isi awal |
| --- | --- | --- |
| `frontend/` | Next.js, TypeScript, Tailwind CSS | Halaman awal dan konfigurasi build |
| `backend/` | Python, FastAPI, Uvicorn | Endpoint `GET /api/health` |
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
| Frontend | Buat Beranda, Eksplorasi, Prediksi & Segmen, serta Evaluasi. Gunakan mock berlabel demo sesuai kontrak. | UI responsif, alur upload, penanganan loading dan error, integrasi API |
| Backend | Implementasikan validasi CSV dan endpoint prediksi dengan respons demo berlabel. | API terdokumentasi, tes validasi, mekanisme pemuatan model, dan pengaturan CORS |
| Data | Verifikasi dataset, kerjakan EDA, lalu bangun baseline klasifikasi, clustering, dan regresi. | Pipeline, versi dependensi, profil segmen, aturan retensi, dan metrik eksperimen |

Target integrasi pertama adalah satu CSV contoh yang bisa diunggah dan menghasilkan respons sesuai kontrak. Setelah itu, hubungkan pipeline terlatih, tampilkan evaluasi tersimpan, lalu ukur waktu prediksi satu pelanggan pada perangkat demo dengan target di bawah tiga detik.

Untuk lingkup awal, gunakan satu dataset publik, training offline, serta rekomendasi retensi berbasis aturan. Proses unggahan untuk satu sesi. Penyimpanan permanen, akun, integrasi billing atau CRM, dan kampanye otomatis berada di luar lingkup awal.
