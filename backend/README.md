# Backend

Folder ini berisi layanan FastAPI untuk menerima CSV, memvalidasi data, menjalankan pipeline yang diserahkan tim Data, dan mengirim hasil ke Frontend. Scaffold menyediakan `GET /api/health`. Petunjuk menjalankan server ada di [README utama](../README.md#menjalankan-scaffold).

## Tugas pertama

Sepakati kolom wajib dan opsional, batas unggahan, format error, serta perlakuan untuk baris invalid dengan tim Frontend dan Data. Lalu siapkan validasi CSV dan respons demo berlabel untuk `POST /api/predictions`. Tunjukkan satu contoh respons sukses dan satu kegagalan validasi yang bisa dijadikan fixture oleh Frontend. Gunakan [usulan kontrak API](../docs/api.md) sebagai titik awal.

## Urutan pengerjaan

1. Terima CSV dan periksa format file, kolom, tipe, nilai kosong, kategori, serta batas ukuran dan jumlah baris sesuai keputusan tim.
2. Bentuk respons demo yang konsisten untuk hasil per pelanggan, metadata, peringatan, dan error. Pertahankan `customerID` agar hasil bisa dicocokkan dengan baris asal.
3. Atur CORS jika UI dan API memakai origin berbeda. Uji upload CSV melalui Frontend dengan respons demo.
4. Muat pipeline terlatih beserta metadata dari tim Data. Jalankan inference dengan preprocessing yang sudah tersimpan di pipeline, terapkan aturan retensi, dan tangani fitur yang tidak lengkap sesuai kontrak.
5. Sediakan metadata model dan evaluasi tersimpan melalui endpoint yang disepakati. Uji alur dengan model terlatih dan ukur waktu dari request hingga respons untuk satu pelanggan pada perangkat demo.

## Hasil serah terima

- API terdokumentasi dengan contoh CSV, respons sukses, dan respons error.
- Layanan inference yang membaca artefak model berversi dan mengembalikan hasil berdasarkan ID pelanggan.
- Tes untuk CSV valid, kolom hilang, tipe data salah, serta kecocokan hasil dengan pelanggan asal.
- Panduan menjalankan server, mengatur CORS, dan memasang versi artefak yang dipilih.
