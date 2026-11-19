# Backend

Layanan FastAPI memvalidasi file churn, menjalankan tiga pipeline dari Data, dan menyediakan ringkasan, prediksi per pelanggan, metadata model, serta hasil eksperimen melalui API.

## Menjalankan FastAPI dan mengecek health

1. Buka PowerShell dari folder utama repo, yaitu folder yang berisi `backend/`, `data/`, dan `frontend/`. Gunakan Python 3.11 atau 3.12.
2. Untuk setup awal, buat virtual environment dan pasang dependensi.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
   ```

3. Jalankan server dengan perintah berikut dan biarkan terminal terbuka.

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
   ```

4. Buka [endpoint health](http://127.0.0.1:8000/api/health) di browser. Pada pemeriksaan lokal, `GET /api/health` mengembalikan HTTP 200 dengan respons berikut.

   ```json
   {"status":"ok"}
   ```

5. Buka [Swagger UI](http://127.0.0.1:8000/docs) untuk melihat dan mencoba endpoint. Tekan `Ctrl+C` di terminal untuk menghentikan server. Jika port 8000 sedang dipakai, tambahkan `--port 8001` ke perintah server dan buka alamat health pada port 8001.

## Memasang file dan model

| Isi | Lokasi bawaan dari root repo | Variabel untuk mengganti lokasi |
| --- | --- | --- |
| CSV churn | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` | `RETENSIGHT_DATASET_PATH` |
| Metadata model dari Data | `backend/artifacts/model_metadata.json` | `RETENSIGHT_MODEL_MANIFEST` |
| Hasil analisis | `backend/results/` | `RETENSIGHT_RESULTS_DIR` |

Paket Data berisi `churn_classifier.joblib`, `customer_clustering.joblib`, `monthly_charges_regressor.joblib`, `model_metadata.json`, dan `evaluations_payload.json`. Backend langsung membaca metadata hasil ekspor Data. Format `manifest.json` sebelumnya tetap dapat dipilih lewat variabel konfigurasi. Saat startup, Backend juga memakai file tersebut jika metadata Data belum tersedia.

### Membuat artefak di komputer sendiri

Letakkan CSV acuan di `data/raw/`, lalu jalankan skrip Data secara offline dari root repo. Jika baru melakukan clone, salinan CSV proyek tersedia di folder `data/`. Buat folder `data/raw/` dan salin file tersebut ke lokasi acuan.

```powershell
New-Item -ItemType Directory -Force data/raw
Copy-Item data/WA_Fn-UseC_-Telco-Customer-Churn.csv data/raw/
.\.venv\Scripts\python.exe data/run_pipeline.py
.\.venv\Scripts\python.exe data/verify_artifacts.py
```

Skrip Data melatih model dan memasang hasilnya ke `backend/artifacts/`. Dependensi Backend memakai daftar versi yang sama dengan folder Data. Jalankan training sebelum menyalakan API.

### Memasang folder yang dikirim tim Data

Jika menerima seluruh `data/outputs/`, letakkan folder tersebut di lokasi lokal dan pasang dengan perintah berikut. Ganti argumen terakhir jika folder kiriman berada di tempat lain.

```powershell
.\.venv\Scripts\python.exe -m backend.install_artifacts data/outputs
```

Perintah ini juga menerima folder yang langsung berisi metadata, tiga model, dan evaluasi. Installer memeriksa dependensi, fitur, serta versi evaluasi sebelum mengganti metadata aktif. Artefak dipasang memakai nama berisi hash, lalu metadata dipublikasikan setelah semua file siap.

Folder CSV mentah, model, keluaran eksperimen, dan hasil batch diabaikan Git. Anggota lain dapat memasang folder kiriman Data atau menjalankan training ulang dengan versi dependensi dan seed yang sesuai. Perintah verifikasi memeriksa kecocokan keluaran pada toleransi pembulatan yang dicatat.

Backend memeriksa file sumber saat server mulai dan setiap dua detik setelah pemeriksaan terakhir selesai. Pasangan versi yang sudah memiliki hasil valid dibaca kembali dari JSON lokal. Jika versi berubah, hasil pasangan baru disimpan sebelum API beralih ke `ready`.

Buka [ringkasan dataset](http://127.0.0.1:8000/api/dataset-summary) untuk melihat status. Jika statusnya `failed`, baca `error` dan versi pada respons, lalu periksa log terminal. Perubahan pada CSV, manifest, atau artefak memicu pemeriksaan ulang. Mulai ulang server jika perbaikannya menyangkut pemasangan dependensi atau izin folder hasil. Endpoint health tetap menunjukkan apakah FastAPI merespons.

Untuk menyesuaikan origin Frontend, setel `RETENSIGHT_FRONTEND_ORIGINS` sebagai daftar alamat yang dipisahkan koma sebelum menjalankan server. Nilai bawaan adalah `http://localhost:3000,http://127.0.0.1:3000`.

Untuk menjalankan tes Backend, pasang dependensi pengembangan lalu jalankan pytest dari root repo.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

## Memverifikasi serah terima

Sesudah artefak terpasang, jalankan perintah berikut dari root repo.

```powershell
.\.venv\Scripts\python.exe -m backend.verify_handover --samples data/outputs/sample_predictions.json
```

Perintah memproses dataset dengan folder hasil sementara, mencocokkan contoh berdasarkan `customerID`, lalu memeriksa pembacaan ulang hasil. Laporan memuat jumlah baris, jumlah sampel cocok, waktu batch, dan waktu pembacaan cache. Jika hanya menerima `backend/artifacts/`, jalankan tanpa `--samples` untuk memakai satu contoh yang disertakan dalam metadata Data.

Gunakan [hasil verifikasi dan panduan Frontend](../docs/backend-handover.md) untuk mencoba endpoint dan memahami bentuk respons.

## Tugas pertama

Gunakan [draf kontrak dataset dan API](../docs/api.md) untuk menyepakati lokasi CSV, versi dataset dan model, tipe kolom, dan penanganan data invalid dengan Data. Cocokkan contoh CSV di draf dengan file dan skema fitur yang diserahkan Data.

Bagikan [fixture dashboard](fixtures/dashboard.demo.json) kepada Frontend untuk mencoba kondisi `ready`, `preparing`, dan `failed`. File JSON berisi respons demo yang dapat dipakai Frontend sebagai mock. Bagian [cara memakai fixture](../docs/api.md#cara-memakai-fixture) memetakan contoh ke tiap endpoint.

## Urutan pengerjaan

1. Baca file dari lokasi yang disepakati tim. Periksa versi dataset, identitas pelanggan, kolom, tipe, serta kecocokan input dengan pipeline.
2. Muat pipeline terlatih dan metadata model dari Data. Jalankan inference dengan preprocessing yang tersimpan, lalu terapkan aturan simulasi rekomendasi retensi. Cocokkan hasil dengan `customerID`.
3. Jalankan pemrosesan otomatis saat dataset dan model pertama kali tersedia, lalu proses ulang saat salah satu versinya berubah. Simpan ringkasan dan hasil per pelanggan beserta kedua versi. Sajikan hasil yang sesuai dengan versi aktif setelah pemrosesan berhasil.
4. Sediakan endpoint baca untuk status, ringkasan, hasil per pelanggan, metadata model, dan evaluasi. Atur CORS jika UI dan API memakai origin berbeda.
5. Uji skenario file tersedia, file hilang atau skema tidak sesuai, hasil sedang disiapkan, dan pergantian versi. Ukur waktu pemrosesan batch dan waktu baca hasil tersimpan secara terpisah.

## Hasil serah terima

- API terdokumentasi dengan contoh ringkasan, hasil per pelanggan, status proses, dan respons error.
- Layanan yang memproses file churn otomatis per versi dataset atau model dan menyajikan hasil tersimpan.
- Tes untuk validasi dataset, kecocokan hasil dengan ID pelanggan, dan pemrosesan ulang saat versi berubah.
- Panduan menjalankan server, memasang dataset dan artefak, mengatur CORS, serta memeriksa kesiapan hasil.
