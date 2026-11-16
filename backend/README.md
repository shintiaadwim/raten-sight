# Backend

Folder ini berisi layanan FastAPI untuk memvalidasi file churn yang dipasang di server, menjalankan pipeline dari tim Data, menyimpan hasil per kombinasi versi dataset dan model, serta menyediakan hasil melalui API. Scaffold menyediakan `GET /api/health`. Petunjuk menjalankan server ada di [README utama](../README.md#menjalankan-scaffold).

## Tugas pertama

Sepakati versi sumber file, skema kolom per model, dan format ringkasan dengan Data dan Frontend. Siapkan cara membaca file yang dipasang di server, lalu bagikan contoh respons berlabel demo untuk hasil siap dan hasil belum siap. Gunakan [usulan kontrak API](../docs/api.md) sebagai titik awal.

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
