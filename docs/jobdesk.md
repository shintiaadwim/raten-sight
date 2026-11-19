# Checklist jobdesk RetenSight

RetenSight menganalisis satu file IBM Telco Customer Churn yang disiapkan tim. Data melakukan eksperimen dan ekspor model secara offline. Backend memproses file di server saat dataset dan model pertama kali tersedia, lalu memproses ulang saat salah satu versinya berubah. Frontend mengambil hasil tersimpan saat dashboard dibuka.

Gunakan checklist ini untuk membagi pekerjaan dan memeriksa hasil serah terima. Nama endpoint, bentuk respons, dan status pemrosesan mengikuti [usulan kontrak API](api.md). Petunjuk menjalankan scaffold ada di [README proyek](../README.md#menjalankan-scaffold).

## 1. Data dan Machine Learning

### Tugas pertama — Verifikasi dataset dan bagikan skema

- [x] Tempatkan file churn acuan di `data/raw/`. Catat nama file, sumber, dan versi dataset yang digunakan tim.
- [x] Periksa jumlah baris dan kolom, distribusi `Churn`, nilai kosong di `TotalCharges`, serta ID yang kosong atau duplikat. Catat jumlah baris sebelum dan sesudah setiap keputusan cleaning yang mengubah jumlah data.
- [x] Buat kamus data berisi nama kolom, arti, tipe, kategori atau rentang nilai, unit, dan contoh. Tandai kolom yang menjadi target, fitur, atau identitas.
- [x] Bagikan daftar fitur dan tipe input **per model**, satu baris contoh dari file acuan, dan cara mencocokkan hasil melalui `customerID` kepada Backend. Bagikan definisi ringkasan untuk grafik eksplorasi kepada Frontend.

### EDA dan preprocessing

- [x] Buat notebook EDA yang memuat jumlah dan proporsi churn, distribusi masa berlangganan dan tagihan, serta distribusi kontrak dan layanan. Catat penyebut untuk setiap persentase agar angka bisa diperiksa.
- [x] Konversi `TotalCharges` ke numerik, periksa nilai kosong setelah konversi, lalu dokumentasikan perlakuan yang dipilih. Jelaskan bagaimana pipeline menangani input serupa saat Backend menjalankan analisis.
- [x] Dokumentasikan perlakuan untuk kategori seperti `No internet service`, `No phone service`, dan kategori yang belum pernah muncul saat fit.
- [x] Pertahankan `customerID` sebagai identitas untuk menyatukan hasil. Keluarkan kolom tersebut dari daftar fitur ketiga model.
- [x] Bungkus imputasi, encoding, scaling, dan estimator dalam pipeline sesuai kebutuhan masing-masing model. Gunakan scaling saat membandingkan metode berbasis jarak seperti KNN dan clustering.
- [x] Untuk klasifikasi dan regresi, buat pembagian awal 80:20 dengan seed tetap. Lakukan stratifikasi berdasarkan `Churn` untuk klasifikasi. Gunakan pembagian dan fold yang sama untuk semua kandidat dalam satu tugas.
- [x] Lakukan tuning melalui CV lima fold pada data latih. Gunakan stratified CV untuk klasifikasi. Di setiap fold, fit preprocessing pada bagian latih fold tersebut. Simpan data uji untuk evaluasi akhir model terpilih.

### Eksperimen klasifikasi churn

- [x] Gunakan `Churn` sebagai target dengan `Yes` sebagai kelas positif. Catat daftar fitur yang dipakai dan pastikan label churn dikeluarkan dari input model.
- [x] Jalankan Dummy Classifier sebagai baseline. Bandingkan Logistic Regression, Decision Tree, Random Forest, KNN, dan Naive Bayes dengan aturan evaluasi yang sama.
- [x] Uji konfigurasi yang relevan, misalnya kedalaman pohon, jumlah tetangga, dan regularisasi. Bandingkan `class_weight` pada algoritma yang mendukungnya. Jika resampling dipilih, terapkan di bagian latih setiap fold.
- [x] Catat rerata dan simpangan baku skor CV per kandidat. Gunakan F1 kelas churn sebagai usulan pembanding utama dan baca recall, precision, serta ROC-AUC untuk memahami hasilnya.
- [x] Tentukan threshold akhir dari prediksi validasi model terpilih. Jelaskan dampaknya terhadap pelanggan churn yang berhasil terdeteksi dan pelanggan bertahan yang ikut ditandai.
- [x] Evaluasi model terpilih pada data uji. Simpan metrik, confusion matrix, kelas positif, dan threshold. Siapkan contoh probabilitas dan label yang konsisten dengan threshold tersebut.

### Eksperimen clustering pelanggan

- [x] Gunakan `tenure`, `MonthlyCharges`, dan `TotalCharges` sebagai fitur awal. Gunakan versi data dan preprocessing yang sama untuk membandingkan algoritma.
- [x] Bandingkan K-Means pada beberapa jumlah klaster dan catat inertia untuk analisis elbow. Uji Agglomerative Clustering pada beberapa jumlah klaster, serta DBSCAN dengan variasi `eps` dan `min_samples`.
- [x] Laporkan silhouette, Davies–Bouldin, dan Calinski–Harabasz jika jumlah klaster memenuhi syarat. Untuk DBSCAN, laporkan jumlah dan persentase titik noise serta cakupan baris yang masuk perhitungan skor.
- [x] Buat profil setiap segmen berdasarkan jumlah pelanggan, masa berlangganan, dan pola tagihan. Gunakan label `Churn` historis setelah klaster terbentuk untuk membaca komposisi churn per segmen.
- [x] Buat pemetaan ID ke nama segmen dan dokumentasikan perlakuan untuk titik noise jika algoritma terpilih menghasilkannya.
- [x] Verifikasi cara memberikan label segmen ketika Backend memproses versi dataset yang dipasang. Jika sebuah kandidat menghasilkan label saat fit, sepakati cara menyerahkan label untuk setiap versi dataset sebelum memilihnya untuk dashboard.

### Eksperimen regresi tagihan bulanan

- [x] Gunakan `MonthlyCharges` sebagai target. Keluarkan `MonthlyCharges`, `TotalCharges`, `Churn`, dan `customerID` dari fitur. Catat satuan biaya dataset.
- [x] Jalankan Dummy Regressor sebagai baseline. Bandingkan Linear Regression, Ridge atau Lasso, Decision Tree Regressor, dan Random Forest Regressor.
- [x] Uji konfigurasi seperti tingkat regularisasi dan kedalaman pohon menggunakan fold yang sama. Simpan rerata dan simpangan baku skor CV per kandidat.
- [x] Gunakan MAE sebagai usulan pembanding utama dan laporkan RMSE serta R². Jelaskan besarnya kesalahan dalam satuan biaya dataset.
- [x] Simpan hasil evaluasi data uji untuk model terpilih. Buat grafik aktual versus prediksi dan grafik residual. Verifikasi pipeline menggunakan contoh input yang hanya memuat fitur regresi.

### Ekspor dan serah terima Data

- [x] Buat tiga tabel eksperimen yang mencantumkan kandidat, parameter, preprocessing, metrik, dan alasan pemilihan model. Beri identitas dataset dan versi model pada setiap hasil yang ditampilkan di dashboard.
- [x] Simpan hasil eksperimen di `data/outputs/`. Siapkan perintah yang dapat dijalankan ulang untuk cleaning, pelatihan, evaluasi, dan ekspor.
- [x] Serahkan file churn berversi, artefak terpilih dengan preprocessing, dan versi dependensi. Gunakan format yang disepakati, misalnya `.joblib`, untuk dipasang oleh Backend di `backend/artifacts/`.
- [x] Sertakan metadata skema fitur, urutan atau tipe fitur yang diperlukan, kelas positif, threshold, pemetaan segmen, profil segmen, satuan biaya, serta sumber evaluasi.
- [x] Susun aturan simulasi retensi. Tulis kondisi risiko dan segmen, rekomendasi yang dihasilkan, urutan aturan saat beberapa kondisi terpenuhi, dan perlakuan saat hasil yang diperlukan belum tersedia.
- [x] Muat ulang artefak pada proses Python baru. Jalankan baris contoh dan cocokkan probabilitas, label churn, segmen, serta estimasi tagihan dengan hasil yang dicatat sebelum ekspor.
- [x] Serahkan contoh hasil per `customerID`, tabel dan data grafik evaluasi, serta catatan setup dependensi. Selesaikan serah terima setelah Backend bisa membaca artefak dan mencocokkan hasil untuk baris contoh.

## 2. Backend

### Tugas pertama — Baca file di server dan siapkan contoh respons

- [x] Jalankan FastAPI dari scaffold dan periksa `GET /api/health`. Catat cara menjalankan server untuk anggota tim lain. [Panduan dan hasil cek lokal](../backend/README.md#menjalankan-fastapi-dan-mengecek-health)
- [x] Cocokkan lokasi file, skema dataset, versi paket, serta penanganan input dengan hasil ekspor Data. Verifikasi contoh per pelanggan agar Data dan Backend membaca kolom dan tipe dengan cara yang sama.
- [x] Siapkan kontrak ringkasan, hasil per pelanggan, metadata, dan pesan error untuk Frontend. Bagikan fixture berlabel demo untuk kondisi hasil siap, sedang disiapkan, dan gagal.
- [ ] Konfirmasi tampilan dan penggunaan respons bersama Frontend saat halaman dashboard sudah terintegrasi.

[Kontrak yang diterapkan](api.md), [fixture demo](../backend/fixtures/dashboard.demo.json), serta [hasil serah terima Backend](backend-handover.md) tersedia untuk tim. Implementasi sudah diuji dengan paket sintetis dan paket terlatih dari skrip Data, termasuk 7.043 pelanggan dan 10 contoh serah terima.

### Validasi dataset dan artefak

- [x] Baca CSV dari lokasi yang disepakati bersama versi dataset. Tangani file hilang, file kosong, CSV yang rusak, dan kolom yang tidak sesuai skema.
- [x] Periksa keberadaan, keunikan, dan konsistensi `customerID`. Validasi tipe dan kolom per pipeline. Ikuti kebijakan Data untuk nilai kosong dan kategori khusus.
- [x] Muat artefak dan metadata dari Data. Periksa kecocokan versi dependensi, daftar fitur, dan kelengkapan metadata yang dibutuhkan untuk menghasilkan respons.
- [x] Siapkan pesan operasional untuk file atau artefak yang gagal diproses. Sertakan versi yang terdampak agar tim bisa menelusuri penyebab kegagalan.

### Inference dan hasil per pelanggan

- [x] Pilih kolom input sesuai kontrak masing-masing model dan gunakan preprocessing yang sudah tersimpan di pipeline.
- [x] Ambil probabilitas untuk kelas churn yang ditetapkan Data. Terapkan threshold dari metadata untuk menghasilkan label prediksi.
- [x] Ambil ID segmen dan cocokkan dengan nama serta profil segmen. Terapkan perlakuan untuk titik noise sesuai metadata jika dibutuhkan.
- [x] Jalankan estimasi tagihan dengan fitur regresi, lalu pakai satuan biaya yang disepakati.
- [x] Jalankan aturan simulasi retensi dari Data menggunakan hasil risiko dan segmen. Gunakan perilaku yang disepakati jika input aturan kurang lengkap.
- [x] Gabungkan ketiga hasil berdasarkan `customerID`. Periksa jumlah pelanggan dan kecocokan ID antara data sumber, ringkasan, dan hasil per pelanggan.

### Pemrosesan otomatis dan penyimpanan hasil

- [x] Jalankan analisis batch saat file dan model pertama kali tersedia. Deteksi perubahan versi dataset atau model dan jadwalkan pemrosesan ulang.
- [x] Gunakan pasangan versi dataset dan model untuk mengenali hasil yang sudah tersedia. Sajikan hasil tersimpan saat Frontend membaca versi yang sama.
- [x] Simpan ringkasan, hasil per pelanggan, dan metadata versi. Tandai hasil siap setelah seluruh keluaran yang akan disajikan telah selesai disimpan.
- [x] Pastikan dua permintaan baca bersamaan dapat menerima status yang konsisten. Perlakukan analisis yang sedang berjalan sebagai `preparing` sesuai usulan kontrak.
- [x] Tangani kegagalan batch dengan status dan pesan yang jelas. Pastikan hasil yang disajikan sebagai versi aktif memang berasal dari versi tersebut.

### Endpoint dan pengujian Backend

- [x] Sediakan `GET /api/dataset-summary` untuk identitas dataset, status, jumlah baris, dan distribusi yang dipakai grafik.
- [x] Sediakan `GET /api/predictions` untuk hasil tersimpan, termasuk ID pelanggan, probabilitas dan label churn, segmen, estimasi tagihan, simulasi rekomendasi, dan metadata versi.
- [x] Sediakan `GET /api/model-info` untuk metadata model. Cocokkan struktur respons dengan fixture Frontend.
- [x] Sediakan `GET /api/evaluations` untuk hasil eksperimen dari Data.
- [x] Atur CORS untuk origin lokal Frontend. Dokumentasikan alamat API, konfigurasi file dan artefak, serta contoh respons untuk kondisi siap, sedang diproses, dan gagal.
- [x] Uji file valid, file hilang, kolom salah, ID duplikat, artefak gagal dimuat, dan hasil dari ketiga pipeline dengan contoh sintetis.
- [x] Uji pembacaan berulang pada versi yang sama dan pemrosesan ulang ketika versi dataset atau model berubah.
- [x] Cocokkan hasil per pelanggan dengan contoh serah terima dari tim Data. Ukur waktu batch dan waktu baca hasil tersimpan pada paket yang diserahkan.

### Hasil serah terima Backend

- [x] API berjalan dengan file churn dan artefak terpilih, beserta dokumentasi endpoint dan contoh respons.
- [x] Panduan pemasangan dataset dan model, cara menjalankan server, serta cara memeriksa status pemrosesan dan versi hasil.
- [x] Hasil uji integrasi Backend menunjukkan kecocokan ID, keberhasilan membaca ulang hasil, dan pergantian versi.
- [ ] Selesaikan uji dashboard bersama Frontend setelah UI berhasil membaca hasil untuk satu versi dataset melalui API.

## 3. Frontend

### Tugas pertama — Buat navigasi dan prototipe Beranda dengan fixture

- [ ] Jalankan scaffold Next.js dari `frontend/`. Siapkan layout dengan navigasi Beranda, Eksplorasi, Prediksi & Segmen, dan Evaluasi Model.
- [ ] Buat fixture sesuai usulan kontrak untuk kondisi hasil siap, sedang disiapkan, dan gagal. Tandai nilai contoh sebagai demo.
- [ ] Buat Beranda yang dapat menampilkan nama dan versi dataset, jumlah pelanggan yang dianalisis, dan status kesiapan hasil. Gunakan fixture untuk menunjukkan setiap kondisi kepada tim.

### Beranda dan Eksplorasi

- [ ] Ambil ringkasan dataset ketika Beranda dibuka. Tampilkan jumlah pelanggan serta jumlah atau proporsi churn historis jika label aktual tersedia.
- [ ] Tampilkan status pemrosesan dari Backend saat hasil belum siap. Perbarui tampilan ketika hasil untuk versi aktif tersedia melalui mekanisme yang disepakati tim.
- [ ] Tautkan Beranda ke Eksplorasi dan Prediksi & Segmen. Saat API gagal dihubungi, tampilkan pesan dan tindakan untuk mencoba memuat kembali.
- [ ] Buat grafik distribusi kontrak, masa berlangganan, dan tagihan berdasarkan format ringkasan yang disepakati. Tampilkan churn historis saat data aktual tersedia.
- [ ] Sertakan judul, satuan sumbu, dan label kategori yang dapat dibaca. Pastikan jumlah atau proporsi pada grafik menggunakan data dari versi yang sama dengan ringkasan.

### Prediksi & Segmen

- [ ] Buat tabel hasil dengan ID pelanggan, probabilitas dan label prediksi churn, nama segmen, estimasi tagihan, dan simulasi rekomendasi.
- [ ] Format probabilitas dari skala 0–1 menjadi persentase. Gunakan label yang jelas untuk churn aktual dan prediksi jika keduanya tampil. Pakai satuan biaya yang disepakati untuk tagihan.
- [ ] Jika profil atau distribusi segmen disediakan, tampilkan nama, ukuran, dan karakteristik segmen. Gunakan istilah yang konsisten dengan metadata Data.
- [ ] Tangani hasil kosong atau nilai yang belum tersedia dengan penjelasan dari API jika ada. Pastikan nilai nol tetap tampil sebagai nilai yang valid.
- [ ] Periksa tabel saat banyak baris atau saat rekomendasi panjang. Pastikan judul kolom dan ID pelanggan tetap mudah dibaca pada layar kecil.

### Evaluasi Model

- [ ] Buat tampilan perbandingan terpisah untuk klasifikasi, clustering, dan regresi. Tampilkan versi model serta sumber data evaluasi.
- [ ] Untuk klasifikasi, tampilkan metrik dan confusion matrix. Tunjukkan threshold model terpilih jika ada di metadata.
- [ ] Untuk clustering, tampilkan metrik internal, jumlah dan profil segmen, serta cakupan atau noise jika dilaporkan.
- [ ] Untuk regresi, tampilkan MAE, RMSE, dan R², beserta grafik aktual versus prediksi dan residual yang disediakan Data.
- [ ] Beri label yang jelas pada skor cross-validation dan skor data uji. Gunakan hasil eksperimen dari API untuk mengisi halaman evaluasi.

### Integrasi dan pengujian Frontend

- [ ] Hubungkan UI ke endpoint ringkasan, hasil pelanggan, metadata, dan evaluasi. Tempatkan alamat API pada konfigurasi yang dapat disesuaikan saat menjalankan aplikasi.
- [ ] Periksa kecocokan versi dataset dan model saat berpindah halaman atau saat Backend memproses versi baru.
- [ ] Uji kondisi loading, hasil siap, data kosong, hasil sedang diproses, error dari API, dan API tidak dapat dihubungi.
- [ ] Uji navigasi pada layar desktop dan ponsel. Periksa penggunaan keyboard, label komponen, keterbacaan grafik, dan kejelasan pesan status.
- [ ] Jalankan pemeriksaan TypeScript dan build produksi. Gunakan file di server untuk uji akhir, lalu cocokkan contoh hasil dashboard dengan respons API.

### Hasil serah terima Frontend

- [ ] Empat halaman responsif dengan navigasi, ringkasan, grafik, tabel hasil, dan tampilan status.
- [ ] Fixture demo untuk pengembangan mandiri serta integrasi dengan hasil nyata dari Backend.
- [ ] Panduan menjalankan UI, mengatur alamat API, dan mendemokan satu analisis dari Beranda hingga Evaluasi Model.

## Checklist integrasi bersama

1. **Kontrak awal.** Data menyerahkan skema dan baris contoh. Backend menyepakati struktur API dan kondisi error. Frontend memeriksa bahwa struktur tersebut cukup untuk ringkasan, tabel, dan grafik.
2. **Integrasi demo.** Backend menyediakan fixture atau respons demo yang disepakati. Frontend mendemokan kondisi siap, sedang diproses, dan gagal. Data mengonfirmasi bahwa istilah, label, dan satuan biaya sesuai dataset.
3. **Integrasi model.** Pasang file dan artefak berversi. Jalankan pemrosesan otomatis, cocokkan contoh baris antara Data, API, dan dashboard, lalu pastikan evaluasi menggunakan hasil eksperimen yang sesuai.
4. **Pemeriksaan akhir.** Buka dashboard berulang kali dengan versi yang sama, ganti salah satu versi, lalu periksa bahwa hasil yang ditampilkan mengikuti versi aktif dan status prosesnya. Catat hasil uji dan bagian yang masih perlu dituntaskan sebelum demo.
