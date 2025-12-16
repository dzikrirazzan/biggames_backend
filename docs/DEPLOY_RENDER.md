# 🚀 Deploy BigGames Backend ke Render + Supabase

Panduan lengkap deploy backend + AI ke Render (free tier) dengan database Supabase (support pgvector).

---

## 📋 Persiapan

### 1. Akun yang Dibutuhkan

- ✅ GitHub account (sudah ada)
- ✅ Render account → Daftar di [render.com](https://render.com) (gratis)
- ✅ Supabase account → Daftar di [supabase.com](https://supabase.com) (gratis)

---

## 🗄️ Setup Database di Supabase

### Step 1: Buat Project Baru

1. Login ke [Supabase Dashboard](https://supabase.com/dashboard)
2. Klik **"New Project"**
3. Isi:
   - **Name**: `biggames-db`
   - **Database Password**: Buat password kuat (simpan baik-baik!)
   - **Region**: `Southeast Asia (Singapore)` (terdekat)
4. Tunggu ~2 menit sampai project ready

### Step 2: Enable pgvector Extension

1. Di dashboard project, klik **SQL Editor** (sidebar kiri)
2. Klik **"New Query"**
3. Paste dan run query ini:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

4. Klik **RUN** (atau Ctrl+Enter)

### Step 3: Dapatkan Connection String

1. Klik **Settings** (gear icon) → **Database**
2. Scroll ke bagian **Connection String** atau **Connection Pooling**
3. Kamu akan lihat 3 opsi - **pilih yang sesuai kebutuhan:**

#### 🎯 Untuk DATABASE_URL (Aplikasi FastAPI):
**Pilih: Transaction Pooler** (Port 6543)
```
postgresql://postgres.xxxxx:password@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```
✅ **Kenapa Transaction?** 
- Cocok untuk web apps dengan banyak request pendek
- Efficient connection pooling
- Recommended untuk SQLAlchemy + FastAPI

#### 🎯 Untuk DATABASE_URL_SYNC (Alembic Migrations):
**Pilih: Direct Connection** (Port 5432)
```
postgresql://postgres.xxxxx:password@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```
✅ **Kenapa Direct?**
- Alembic butuh akses penuh untuk schema changes
- Migrations tidak butuh pooling

❌ **Jangan pakai Session Pooler** - itu untuk long-lived connections, bukan untuk web apps.

**PENTING:**
- Ganti `[YOUR-PASSWORD]` dengan password yang kamu buat tadi
- Simpan 2 versi dengan prefix berbeda:
  - **DATABASE_URL** (async untuk app): `postgresql+asyncpg://...pooler.supabase.com:6543/postgres`
  - **DATABASE_URL_SYNC** (sync untuk alembic): `postgresql://...pooler.supabase.com:5432/postgres`

---

## 🌐 Deploy Backend ke Render

### Step 1: Push Code ke GitHub

```bash
# Pastikan semua file sudah di commit
git add .
git commit -m "Add render.yaml and deployment configs"
git push origin main
```

### Step 2: Connect Render ke GitHub

1. Login ke [Render Dashboard](https://dashboard.render.com)
2. Klik **"New +"** → **"Web Service"**
3. Pilih **"Build and deploy from a Git repository"**
4. Klik **"Connect GitHub"** (authorize akses)
5. Cari dan pilih repo: `dzikrirazzan/biggames_backend`
6. Klik **"Connect"**

### Step 3: Konfigurasi Service

Render akan auto-detect `render.yaml`, tapi cek settingan:

#### Basic Settings:

- **Name**: `biggames-backend` (atau nama lain)
- **Region**: `Singapore`
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: (sudah di render.yaml)
- **Start Command**: (sudah di render.yaml)
- **Plan**: **Free**

#### Environment Variables (WAJIB):

Render sudah baca dari `render.yaml`, tapi kamu harus isi manual:

1. **DATABASE_URL** (Async - untuk app):

```
postgresql+asyncpg://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```
☝️ **Port 6543** (Transaction Pooler)

2. **DATABASE_URL_SYNC** (Sync - untuk alembic):

```
postgresql://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```
☝️ **Port 5432** (Direct Connection)

3. **JWT_SECRET_KEY**: (Generate otomatis atau buat sendiri)

```bash
# Generate di terminal:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Variabel lain (QRIS, Bank, dll) bisa diubah nanti sesuai kebutuhan.

### Step 4: Deploy!

1. Scroll ke bawah, klik **"Create Web Service"**
2. Render akan mulai build (~5-10 menit pertama kali):
   - Install dependencies
   - Download model Hugging Face (~400MB)
   - Run migrations
   - Start server

### Step 5: Cek Status

- **Logs**: Lihat di tab **"Logs"** untuk monitor progress
- **Events**: Tab **"Events"** untuk status deployment
- Tunggu sampai muncul: `✅ Live`

---

## 🧪 Testing Deployment

### 1. Dapatkan URL

Setelah deploy sukses, Render kasih URL seperti:

```
https://biggames-backend.onrender.com
```

### 2. Test Health Check

```bash
# Ganti dengan URL kamu
curl https://biggames-backend.onrender.com/
```

Response:

```json
{ "message": "Welcome to BIG GAMES Online Booking API" }
```

### 3. Test Endpoints

```bash
# Docs
https://biggames-backend.onrender.com/docs

# Redoc
https://biggames-backend.onrender.com/redoc
```

---

## 🌱 Seed Data (Opsional)

Kalau mau isi data demo:

### Via Render Shell:

1. Di dashboard Render, klik tab **"Shell"**
2. Run command:

```bash
python scripts/seed_demo_data.py
```

### Via Local Connection:

```bash
# Export database URL dari Supabase
export DATABASE_URL="postgresql://postgres.xxxxx:password@..."

# Run seed script
python scripts/seed_demo_data.py
```

---

## 🔐 Security Checklist

- [ ] Ganti `JWT_SECRET_KEY` dengan value yang aman
- [ ] Set `DEBUG=false` di production
- [ ] Update payment info (QRIS, Bank) dengan data asli
- [ ] Jangan commit `.env` file ke GitHub
- [ ] Database password disimpan aman (jangan share)

---

## ⚠️ Keterbatasan Free Tier

### Render Free Tier:

- ✅ 512MB RAM (cukup untuk model MiniLM)
- ✅ Shared CPU
- ⚠️ **Sleep setelah 15 menit tidak ada traffic** (cold start ~30 detik)
- ✅ 750 jam/bulan (cukup untuk 1 service 24/7)

### Supabase Free Tier:

- ✅ 500MB database storage
- ✅ pgvector extension support ✨
- ✅ 2GB bandwidth/bulan
- ⚠️ Project pause setelah 1 minggu inaktif (bisa wake up manual)

### Tips Mengatasi Cold Start:

Buat Cron Job sederhana untuk "ping" setiap 10 menit:

```bash
# Render Cron Job (free)
# Endpoint: GET https://biggames-backend.onrender.com/
# Schedule: */10 * * * * (setiap 10 menit)
```

---

## 🐛 Troubleshooting

### Build Failed - Model Download Timeout

**Error**: `Timeout downloading model`

**Solusi**: Render free tier bisa lambat. Coba:

1. Restart deployment
2. Atau comment out auto-download, upload model manual nanti

### Database Connection Error

**Error**: `Connection refused` atau `SSL required`

**Solusi**:

- Pastikan connection string pakai format yang benar
- Supabase butuh `?sslmode=require` di akhir URL kalau error SSL

### Service Sleep (Cold Start)

**Symptom**: Request pertama lambat (~30s)

**Solusi**:

- Normal untuk free tier
- Setup Cron Job untuk keep-alive (lihat tips di atas)

---

## 📱 Next Steps

Setelah backend live:

1. **Update Frontend** (kalau ada): Ganti API base URL
2. **Generate Embeddings**: Run script untuk generate room embeddings
3. **Setup Monitoring**: Gunakan Render logs untuk monitor errors
4. **Custom Domain** (opsional): Bisa pakai domain sendiri

---

## 🆘 Butuh Bantuan?

- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
- pgvector Guide: https://github.com/pgvector/pgvector

---

**Happy deploying! 🎮🚀**
