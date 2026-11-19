# Frontend RetenSight

Dashboard Next.js, TypeScript, dan Tailwind CSS untuk membaca hasil analisis file churn dari Backend. Empat bagian tersedia melalui navigasi Beranda, Eksplorasi, Prediksi & Segmen, dan Evaluasi Model.

## Menjalankan lokal

Jalankan Backend dan pasang paket Data sesuai [panduan Backend](../backend/README.md). Dari folder `frontend/`, gunakan Node.js 20.9 atau lebih baru.

```powershell
npm ci
npm run dev
```

Buka [dashboard lokal](http://localhost:3000). Untuk mengganti alamat Backend, setel variabel sebelum menjalankan dev server atau build.

```powershell
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run dev
```

Jika port Frontend diganti, tambahkan origin yang dipakai browser ke `RETENSIGHT_FRONTEND_ORIGINS` pada terminal Backend sebelum menjalankan Uvicorn. Contoh konfigurasi untuk Frontend pada port 3100 adalah sebagai berikut.

```powershell
$env:RETENSIGHT_FRONTEND_ORIGINS = "http://localhost:3100,http://127.0.0.1:3100"
```

## Alur penggunaan

1. Buka Beranda untuk melihat identitas dataset, jumlah pelanggan, churn historis, dan versi analisis.
2. Pilih Eksplorasi untuk membaca distribusi kontrak, masa berlangganan, dan tagihan.
3. Pilih Prediksi & Segmen untuk melihat distribusi segmen serta tabel hasil. Tabel menampilkan 25 pelanggan per halaman. Informasi model, fitur, threshold, dan satuan biaya tersedia pada bagian yang dapat dibuka di bawah tabel.
4. Pilih Evaluasi Model untuk membandingkan algoritma, membaca confusion matrix, profil segmen, grafik elbow, aktual versus prediksi, dan residual. Setiap kelompok mencantumkan sumber evaluasi.

Dashboard memeriksa status setiap dua detik saat hasil sedang disiapkan, dan memuat ulang hasil setiap sepuluh detik setelahnya. Respons yang berbeda versi ditahan sampai pasangan versi konsisten. Tombol Muat ulang bisa dipakai setelah memperbaiki koneksi atau berkas input.

Label `Data demo` tampil jika API mengirim `is_demo: true`. Nilai aktual, prediksi, data latih cross-validation, dan data uji memiliki label terpisah.

## Pemeriksaan pengembangan

```powershell
npm run check
npm test
npm run build
npm start
```

Tes memakai Node test runner dan dependensi TypeScript yang sudah tersedia. Kasusnya mencakup status proses, error terstruktur, koneksi gagal, data kosong, serta versi dataset atau model yang berbeda.

Fixture berada di [src/mocks/dashboard.json](src/mocks/dashboard.json). Fixture menyediakan contoh `ready`, `preparing`, dan `failed`; objek `ready.evaluations` berisi contoh evaluasi untuk pengembangan UI. Gunakan bentuk respons sesuai [kontrak API](../docs/api.md).
