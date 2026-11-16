# Frontend

Folder ini berisi aplikasi Next.js, TypeScript, dan Tailwind CSS. Tim Frontend mengerjakan navigasi, ringkasan file churn, grafik eksplorasi, tampilan hasil, dan integrasi API. Scaffold menyediakan satu halaman awal. Petunjuk menjalankannya ada di [README utama](../README.md#menjalankan-scaffold).

## Menjalankan Frontend

```bash
cd frontend
npm install
npm run dev
```

Buka [http://localhost:3000](http://localhost:3000) di browser.

## Tugas pertama

Buat navigasi Beranda, Eksplorasi, Prediksi & Segmen, dan Evaluasi. Mulai dari Beranda yang menampilkan nama dan versi dataset, jumlah pelanggan yang dianalisis, dan churn aktual jika label tersedia. Siapkan juga tampilan saat hasil sedang disiapkan atau gagal tersedia. Gunakan fixture berlabel demo sesuai [usulan kontrak API](../docs/api.md) dan cocokkan dengan respons Backend saat tersedia.

## Urutan pengerjaan

1. Siapkan layout responsif dan navigasi. Saat Beranda dibuka, ambil ringkasan dari API dan tampilkan status jika hasil belum siap.
2. Bangun halaman Eksplorasi untuk distribusi masa berlangganan, kontrak, tagihan, dan churn historis. Gunakan ringkasan dari versi dataset yang aktif.
3. Buat halaman Prediksi & Segmen. Tampilkan probabilitas dan label churn, segmen, estimasi dalam satuan biaya dataset, serta simulasi rekomendasi per pelanggan. Beri label yang jelas untuk nilai aktual dan hasil model jika keduanya ditampilkan.
4. Buat halaman Evaluasi untuk perbandingan model, metrik, dan grafik dari eksperimen tersimpan. Cantumkan versi model dan sumber evaluasi.
5. Hubungkan UI ke API dan uji dashboard saat hasil tersedia, sedang disiapkan, atau gagal dimuat. Periksa tampilan dan navigasi pada layar kecil.

## Hasil serah terima

- Empat halaman responsif yang terhubung ke API.
- Komponen ringkasan dataset, tabel hasil, dan grafik yang dapat dipakai ulang.
- Fixture berlabel demo untuk kondisi hasil siap, sedang diproses, dan gagal.
- Panduan menjalankan Frontend dan mengatur alamat API, beserta langkah uji dashboard dengan dataset yang dipasang di server.
