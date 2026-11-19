# Serah terima Backend RetenSight

Backend memakai file churn lokal dan paket yang diekspor oleh `data/run_pipeline.py`. Hasil analisis disimpan sebagai JSON di `backend/results/` dan disajikan melalui FastAPI.

## File yang diperlukan

| File | Sumber |
| --- | --- |
| `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` | Salinan CSV acuan tim Data |
| `backend/artifacts/model_metadata.json` | Metadata hasil ekspor Data |
| Tiga file `.joblib` yang dirujuk metadata | Pipeline klasifikasi, clustering, dan regresi hasil training |
| File evaluasi yang dirujuk metadata | `evaluations_payload.json` hasil eksperimen Data, atau nama berisi hash setelah pemasangan |

File mentah, model, keluaran eksperimen, dan hasil batch diabaikan Git. Kode installer dan verifikasi ikut masuk Git. Lihat [panduan Backend](../backend/README.md) untuk membuat artefak ulang atau memasang folder kiriman Data.

## Kontrak dengan Data

- Metadata memberi nama dan urutan fitur untuk setiap pipeline. Backend memeriksa fitur dan versi dependensi sebelum inference.
- Nilai `TotalCharges` yang kosong diteruskan sebagai nilai hilang. Pipeline ekspor Data menangani kondisi itu dengan imputasi nol, sesuai cleaning yang dipakai saat training.
- Label model churn adalah angka `0` dan `1`. Metadata menyebut makna kelas positif sebagai `Yes`. Adapter menghubungkan kelas angka `1` dengan churn dan menerapkan threshold dari metadata.
- Hasil dipadankan melalui `customerID`. Data menyediakan contoh untuk probabilitas churn, label, segmen, nama segmen, estimasi tagihan, dan rekomendasi.
- Aturan simulasi retensi dibaca dari metadata dan dijalankan menurut prioritas. Evaluasi mempertahankan sumber data uji dan perbandingan algoritma yang dibuat Data.

## Kontrak dengan Frontend

Jalankan server lalu coba endpoint melalui [Swagger lokal](http://127.0.0.1:8000/docs).

| Endpoint | Fungsi untuk dashboard |
| --- | --- |
| `GET /api/health` | Memeriksa apakah server merespons |
| `GET /api/dataset-summary` | Ringkasan dataset dan kesiapan hasil |
| `GET /api/predictions` | Hasil model per pelanggan |
| `GET /api/model-info` | Algoritma, fitur, threshold, profil segmen, dan satuan biaya |
| `GET /api/evaluations` | Perbandingan algoritma, metrik, dan data grafik eksperimen |

Gunakan `status` untuk menampilkan kondisi `preparing`, `ready`, atau `failed`. Baca `data` saat hasil siap. Untuk kondisi gagal, tampilkan `error.message`. Jika API sedang menyiapkan versi baru, muat kembali ringkasan sampai hasil siap.

Pastikan `dataset_version` dan `model_version` cocok sebelum menggabungkan respons dari beberapa endpoint. Keduanya berada pada envelope respons. Versi di dalam isi evaluasi adalah nama rilis sumber dari Data.

Frontend dapat memakai [fixture demo](../backend/fixtures/dashboard.demo.json) untuk kondisi siap, sedang diproses, dan gagal. Perbandingan algoritma dapat diambil langsung dari endpoint evaluasi setelah paket Data terpasang. Struktur field dijelaskan di [kontrak API](api.md).

## Hasil pemeriksaan lokal 19 November 2026

Paket dibuat dengan skrip Data yang ada di repo, lalu diperiksa melalui API menggunakan Uvicorn. Lingkungan pemeriksaan memakai Python 3.12.14, NumPy 2.2.6, pandas 2.2.3, scikit-learn 1.6.1, dan joblib 1.4.2.

- CSV memiliki 7.043 pelanggan. Ringkasan membaca 1.869 label churn `Yes` dan 5.174 label `No`.
- Sepuluh contoh dari `sample_predictions.json` cocok berdasarkan ID. Label, segmen, nama segmen, dan rekomendasi cocok persis. Probabilitas dibandingkan dengan toleransi absolut 0,0001 dan estimasi tagihan dengan toleransi 0,01 sesuai pembulatan keluaran Data.
- Endpoint evaluasi memuat 14 kandidat klasifikasi, 14 kandidat clustering, dan 13 kandidat regresi.
- Pembacaan ringkasan berulang memakai satu file hasil tersimpan dengan waktu modifikasi yang tetap.
- Sebanyak 53 tes otomatis lulus, mencakup kegagalan input, versi paket yang berbeda, hasil sedang disiapkan, dan pemulihan setelah file diperbaiki. Uji HTTP juga memeriksa CORS untuk origin Frontend lokal.

| Pengukuran | Waktu pada pemeriksaan lokal |
| --- | --- |
| Batch awal 7.043 pelanggan pada folder hasil kosong | 2,7808 detik |
| Memuat ulang batch dari cache | 0,0525 detik |
| HTTP ringkasan dataset saat hasil siap | 2,93 ms |
| HTTP seluruh prediksi pelanggan saat hasil siap | 98,74 ms |
| HTTP metadata model saat hasil siap | 3,33 ms |
| HTTP hasil evaluasi saat hasil siap | 3,79 ms |

Angka ini berasal dari satu pemeriksaan lokal. Jalankan ulang verifikasi pada perangkat demo untuk mendapatkan waktunya.

```powershell
.\.venv\Scripts\python.exe -m backend.verify_handover --samples data/outputs/sample_predictions.json
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Integrasi tampilan dashboard diperiksa bersama Frontend setelah halaman UI tersedia.
