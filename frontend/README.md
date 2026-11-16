# Frontend

Folder ini berisi aplikasi Next.js, TypeScript, dan Tailwind CSS. Tim Frontend mengerjakan navigasi, upload CSV, visualisasi, tampilan hasil, serta integrasi API. Scaffold menyediakan satu halaman awal. Petunjuk menjalankannya ada di [README utama](../README.md#menjalankan-scaffold).

## Tugas pertama

Buat navigasi Beranda, Eksplorasi, Prediksi & Segmen, dan Evaluasi. Mulai dari Beranda dengan pemilih CSV, tombol unggah, dan tampilan status. Gunakan fixture berlabel demo untuk mensimulasikan respons sukses dan error berdasarkan [usulan kontrak API](../docs/api.md). Cocokkan fixture dengan contoh respons tim Backend saat tersedia.

## Urutan pengerjaan

1. Siapkan layout responsif dan navigasi, lalu buat alur unggah dengan status awal, loading, sukses, dan error.
2. Bangun halaman Eksplorasi untuk ringkasan dan distribusi data. Tampilkan state kosong sebelum ada hasil unggahan. Sepakati sumber ringkasan dengan Backend.
3. Buat halaman Prediksi & Segmen. Tampilkan hasil per pelanggan, probabilitas dan label churn, segmen, estimasi tagihan dalam satuan dataset, serta rekomendasi retensi. Jelaskan jika hasil tertentu tidak tersedia karena fitur input kurang.
4. Buat halaman Evaluasi untuk perbandingan model, metrik, dan grafik dari hasil eksperimen tersimpan.
5. Hubungkan UI ke API, uji satu CSV contoh dari awal sampai hasil, lalu periksa responsivitas serta pesan validasi.

## Hasil serah terima

- Empat halaman responsif yang terhubung ke API.
- Komponen upload, tabel hasil, dan grafik yang dapat dipakai ulang.
- Fixture sukses dan error berlabel demo untuk pengembangan mandiri.
- Panduan menjalankan Frontend dan mengatur alamat API, beserta langkah uji upload CSV.
