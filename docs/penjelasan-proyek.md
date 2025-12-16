# BigGames Online Booking System — Penjelasan Santai

Proyek ini adalah backend + AI untuk sistem booking ruangan gaming bernama **BigGames**. Tidak ada urusan frontend di sini—semua fokus ke logika server, database, dan mesin rekomendasi.

## 1) Gambaran Umum

BigGames menyediakan banyak tipe ruangan (PS, PC, VR, kapasitas beda-beda). Masalah klasik: user suka bingung milih. Ide besarnya: pakai AI supaya rekomendasi terasa personal dan cepat, bukan sekadar daftar panjang. AI dipakai karena:

- User butuh arahan; pilihan terlalu banyak bikin ragu.
- AI bisa membaca deskripsi ruangan dan kebiasaan user, lalu menyarankan opsi yang relevan.
- Bisa jalan otomatis tanpa survei manual ke user.

## 2) Gambaran Backend (garis besar)

- Framework: **FastAPI (Python)**, REST endpoints.
- Database: **PostgreSQL** dengan ekstensi **pgvector** buat operasi vektor.
- Tugas backend:
  - Simpan data ruangan + detailnya.
  - Catat aktivitas user (lihat, klik, booking, rating).
  - Jalankan AI recommendation dan balikin daftar ruangan yang cocok.
- Tabel utama (tanpa detail SQL): `rooms`, `room_embeddings`, `user_events`, `reservations`, `reviews`.
- Intinya: backend ini pusat logika + AI, bukan cuma CRUD. Ada pipeline embedding, perhitungan vektor user, re-ranking, dan handling cold start.

## 3) Penjelasan AI (paling penting)

### 3.1 Ide dasar

Bayangin sistem ini "mengingat" dua hal: karakter setiap ruangan dan kebiasaan tiap user. Lalu sistem mencocokkan keduanya untuk cari kecocokan terbaik.

### 3.2 Content-Based Filtering (profil ruangan)

- Setiap ruangan diubah jadi **"sidik jari digital"** berupa vektor angka (embedding).
- Sidik jari dibuat dari deskripsi ruangan: nama, kategori, kapasitas, harga, konsol yang tersedia, dll.
- Model yang dipakai: **Hugging Face sentence-transformers paraphrase-multilingual-MiniLM-L12-v2** (mendukung Bahasa Indonesia, gratis, jalan offline di server, 384 dimensi).
- Analogi: kayak Spotify tahu lagu A mirip lagu B karena pola suaranya, bukan karena judul saja.

### 3.3 Collaborative Filtering (perilaku user)

- Sistem nyatet event: lihat ruangan, klik, booking, kasih rating. Booking dan rating punya bobot paling tinggi.
- Dari event itu, sistem bikin **vektor preferensi user** (rata-rata tertimbang embedding ruangan yang pernah disentuh).
- Jadi AI belajar dari kebiasaan nyata, bukan dari form tanya-jawab.

### 3.4 Popularity-Based (user baru)

- Kalau user baru (riwayat < 3 event), sistem belum kenal seleranya.
- Solusi cold start: tampilkan ruangan paling sering dibooking dan rating bagus dalam 30 hari terakhir.

### 3.5 Re-ranking cepat

- Setelah dapat kandidat ruangan, sistem gabungkan skor kemiripan + rating + popularitas + kecocokan harga + sedikit faktor "freshness". Hasil akhir tetap relevan sekaligus berkualitas.

## 4) Alur Kerja (versi manusia)

1. User minta rekomendasi.
2. Backend cek: user baru atau sudah punya riwayat?
3. Kalau baru → pakai daftar populer. Kalau sudah ada riwayat → hitung vektor preferensi dari event-eventnya.
4. AI cari ruangan paling mirip (content + collaborative), lalu re-rank dengan rating/popularitas/harga.
5. Kalau user kasih rentang waktu, backend pastikan ruangan tidak bentrok jadwal.
6. Hasil dikirim ke user. Proses ini cepat (sekitar **0.2 detik** di server sendiri, tanpa call API eksternal).

## 5) Kenapa pakai model ini

- **Bahasa Indonesia**: model multilingual, jadi deskripsi lokal kebaca baik.
- **Tanpa biaya per-call**: model di-host sendiri; tidak ketergantungan API berbayar.
- **Data aman**: teks ruangan dan jejak user tidak dikirim keluar server.
- **Cukup cepat**: MiniLM ringan, bisa real-time di CPU.

## 6) Intinya proyek ini apa

Ini bukan AI super rumit, tapi AI yang kepakai. Backend + AI saling dukung: backend menyimpan data dan event, AI mengolah embedding + preferensi untuk rekomendasi yang terasa personal. Cocok untuk tugas kuliah karena jelas ada elemen AI, ada backend nyata, dan alur sistem yang bisa dijelaskan ke dosen dengan bahasa sehari-hari.

## Cara menjelaskan ke dosen (lisan, singkat)

"BigGames itu backend sistem booking ruangan gaming. Kita pakai FastAPI + PostgreSQL. Setiap ruangan diubah jadi embedding supaya mesin ngerti karakternya. Perilaku user (lihat, klik, booking, rating) dikonversi ke vektor preferensi. Kalau user lama, rekomendasi pakai kecocokan vektor; kalau baru, pakai ruangan paling populer. Semuanya jalan di server sendiri, cepat, dan aman tanpa API eksternal."
