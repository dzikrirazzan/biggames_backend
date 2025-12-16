# 🚀 Deploy BigGames Backend ke Heroku + Supabase

Panduan lengkap deploy backend + AI ke Heroku dengan database Supabase (support pgvector).

---

## ⚠️ Penting: Heroku Free Tier

**Update November 2022:** Heroku sudah menghapus free tier. Opsi yang tersedia:

1. **Eco Dyno** - $5/bulan (500 MB RAM, tidak sleep)
2. **Basic Dyno** - $7/bulan (512 MB RAM)
3. **Standard Dyno** - $25/bulan (1 GB RAM, recommended untuk production)

**Alternative Free:**
- Railway.app (free $5 credit/bulan)
- Fly.io (free tier tersedia)
- Render.com (free tier tersedia) - lihat [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

---

## 📋 Persiapan

### 1. Akun yang Dibutuhkan
- ✅ GitHub account (sudah ada)
- ✅ Heroku account → Daftar di [heroku.com](https://heroku.com) (perlu CC untuk Eco Dyno)
- ✅ Supabase account → Daftar di [supabase.com](https://supabase.com) (gratis)
- ✅ Heroku CLI → Install: `brew tap heroku/brew && brew install heroku` (Mac)

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
3. Copy 2 versi:

#### Untuk DATABASE_URL (Transaction Pooler - Port 6543):
```
postgresql://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

#### Untuk DATABASE_URL_SYNC (Direct Connection - Port 5432):
```
postgresql://postgres.xxxxx:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

**Simpan keduanya!** Nanti dipakai di Heroku config vars.

---

## 🌐 Deploy Backend ke Heroku

### Step 1: Install Heroku CLI (kalau belum)

**Mac:**
```bash
brew tap heroku/brew && brew install heroku
```

**Linux/WSL:**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

**Windows:**
Download installer dari [heroku.com/cli](https://devcenter.heroku.com/articles/heroku-cli)

### Step 2: Login ke Heroku

```bash
heroku login
```

Browser akan terbuka, login dengan akun Heroku kamu.

### Step 3: Buat Heroku App

```bash
cd /Users/dzikrirazzan/code/biggames_backend

# Buat app baru (nama harus unique)
heroku create biggames-backend
# atau biarkan Heroku generate random name:
# heroku create
```

Output:
```
Creating ⬢ biggames-backend... done
https://biggames-backend-xxxxx.herokuapp.com/ | https://git.heroku.com/biggames-backend.git
```

### Step 4: Set Environment Variables

```bash
# Database URLs (ganti dengan string Supabase kamu)
heroku config:set DATABASE_URL="postgresql+asyncpg://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

heroku config:set DATABASE_URL_SYNC="postgresql://postgres.xxxxx:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres"

# Generate JWT Secret
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
heroku config:set JWT_SECRET_KEY="$JWT_SECRET"

# Other configs
heroku config:set JWT_ALGORITHM="HS256"
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES="30"
heroku config:set REFRESH_TOKEN_EXPIRE_DAYS="7"
heroku config:set DEBUG="false"
heroku config:set APP_NAME="BIG GAMES Online Booking"

# Payment info (ganti dengan yang asli nanti)
heroku config:set QRIS_IMAGE_URL="https://example.com/qris-biggames.png"
heroku config:set BANK_NAME="BCA"
heroku config:set BANK_ACCOUNT_NUMBER="1234567890"
heroku config:set BANK_ACCOUNT_NAME="BIG GAMES Online Booking"
```

### Step 5: Deploy!

```bash
# Push ke Heroku
git push heroku main

# Atau kalau branch bukan main:
# git push heroku master
```

Heroku akan:
1. Detect bahasa Python (dari `runtime.txt`)
2. Install dependencies (dari `requirements.txt`)
3. Download model Hugging Face (~400MB) - **ini akan lama ~5-10 menit pertama kali**
4. Run migrations (dari `Procfile`)
5. Start server

### Step 6: Cek Status & Logs

```bash
# Cek app running
heroku ps

# Lihat logs real-time
heroku logs --tail

# Open app di browser
heroku open
```

---

## 🧪 Testing Deployment

### 1. Test Health Check

```bash
# Ganti dengan URL Heroku kamu
curl https://biggames-backend-xxxxx.herokuapp.com/
```

Response:
```json
{"message": "Welcome to BIG GAMES Online Booking API"}
```

### 2. Test API Docs

Buka di browser:
```
https://biggames-backend-xxxxx.herokuapp.com/docs
```

---

## 🌱 Seed Data & Generate Embeddings

### Via Heroku Run (Recommended)

```bash
# Seed demo data
heroku run python scripts/seed_demo_data.py

# Generate embeddings untuk semua ruangan
heroku run python scripts/generate_embeddings.py
```

### Via Heroku Bash (Interactive)

```bash
# Masuk ke bash
heroku run bash

# Di dalam bash:
python scripts/seed_demo_data.py
python scripts/generate_embeddings.py
exit
```

---

## 🔧 Commands Berguna

### Restart App
```bash
heroku restart
```

### View Config Vars
```bash
heroku config
```

### Update Config Var
```bash
heroku config:set VARIABLE_NAME="value"
```

### Run Commands di Heroku
```bash
heroku run python scripts/your_script.py
```

### Connect ke Database (Supabase)
```bash
# Sudah pakai Supabase, jadi tidak perlu Heroku Postgres addon
```

### Scale Dynos
```bash
# Lihat dyno status
heroku ps

# Scale web dyno
heroku ps:scale web=1
```

---

## 💰 Pricing & Dyno Info

### Eco Dyno ($5/bulan)
- 512 MB RAM ⚠️ (mungkin tidak cukup untuk model AI + traffic tinggi)
- Shared CPU
- **Tidak sleep** (always on)
- Recommended untuk development/testing

### Basic Dyno ($7/bulan)
- 512 MB RAM
- Dedicated CPU
- Tidak sleep
- Auto-restart

### Standard 1X ($25/bulan)
- **1 GB RAM** ✅ (recommended untuk production dengan AI)
- Dedicated CPU
- Tidak sleep
- Better performance

**Pilih dyno:**
```bash
# Set ke Eco (default untuk baru)
heroku ps:type eco

# Upgrade ke Standard (recommended untuk AI)
heroku ps:type standard-1x
```

---

## 🐛 Troubleshooting

### Build Failed - Slug Size Too Large

**Error:** `Compiled slug size: 600M is too large (max is 500M)`

**Solusi:** Model Hugging Face (~400MB) + dependencies bisa lewat batas. Opsi:

1. **Gunakan model lebih kecil** (edit `app/services/embedding.py`)
2. **Upload model ke cloud storage** (S3/GCS) dan download saat runtime
3. **Ignore model dari git** (sudah di `.gitignore`)

### Timeout During Deployment

**Error:** Model download timeout saat build

**Solusi:**
```bash
# Set build timeout lebih lama
heroku config:set BUILD_TIMEOUT=1800
```

### Database Connection Error

**Error:** `Connection refused` atau `SSL required`

**Solusi:** 
- Pastikan connection string dari Supabase benar
- Cek apakah Supabase project masih aktif
- Tambahkan `?sslmode=require` di akhir URL kalau perlu:
  ```bash
  heroku config:set DATABASE_URL_SYNC="postgresql://...?sslmode=require"
  ```

### App Crashing - R14 (Memory Quota Exceeded)

**Error:** `Error R14 (Memory quota exceeded)`

**Solusi:**
- Model Hugging Face + dependencies butuh ~400-600MB RAM
- **Upgrade ke Standard 1X dyno** (1GB RAM):
  ```bash
  heroku ps:type standard-1x
  ```

### Slow First Request (Cold Start)

**Symptom:** Request pertama lambat ~30-60 detik

**Solusi:**
- Model loading saat startup
- Eco/Basic dyno tidak sleep, jadi hanya lambat saat restart
- Atau setup warm-up request saat startup

---

## 📱 CI/CD with GitHub (Optional)

### Enable Auto-Deploy dari GitHub

1. Login ke [Heroku Dashboard](https://dashboard.heroku.com)
2. Pilih app **biggames-backend**
3. Tab **Deploy** → **Deployment method** → Connect to GitHub
4. Search repo: `dzikrirazzan/biggames_backend`
5. Enable **Automatic deploys** dari branch `main`

Sekarang setiap push ke GitHub akan auto-deploy ke Heroku! 🎉

---

## 🔐 Security Checklist

- [x] Environment variables di-set lewat Heroku config (tidak di code)
- [x] `DEBUG=false` di production
- [x] JWT secret unique dan aman
- [x] Database password kuat
- [x] `.env` tidak di-commit ke git
- [x] Payment info (QRIS, Bank) diupdate dengan data asli

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time logs
heroku logs --tail

# Last 200 lines
heroku logs -n 200

# Filter errors only
heroku logs --tail | grep ERROR
```

### Add-ons untuk Monitoring (Optional)

```bash
# Papertrail (free tier: 50MB log/bulan)
heroku addons:create papertrail:chokladfabriken

# New Relic (monitoring)
heroku addons:create newrelic:wayne
```

---

## 📈 Performance Tips

### 1. Enable HTTP/2
Already enabled by Heroku, nothing to do.

### 2. Gzip Compression
FastAPI sudah handle ini by default.

### 3. Database Connection Pool
SQLAlchemy async pool sudah dikonfigurasi di `app/db/session.py`.

### 4. Caching (Advanced)
Bisa tambahkan Redis add-on untuk cache:
```bash
heroku addons:create heroku-redis:mini
```

---

## 🆘 Butuh Bantuan?

- Heroku Docs: https://devcenter.heroku.com/
- Supabase Docs: https://supabase.com/docs
- pgvector Guide: https://github.com/pgvector/pgvector
- Heroku Python Guide: https://devcenter.heroku.com/articles/getting-started-with-python

---

## 🔄 Alternative: Deploy ke Railway (Free Option)

Kalau budget ketat, Railway punya free tier:

1. Signup di [railway.app](https://railway.app)
2. Connect GitHub repo
3. Deploy (mirip Heroku tapi free $5 credit/bulan)
4. Setup sama: environment variables + Supabase

---

## 📝 Summary Commands

```bash
# Setup
heroku login
heroku create biggames-backend
heroku config:set DATABASE_URL="..."
# ... set all env vars

# Deploy
git push heroku main

# Post-deploy
heroku run python scripts/seed_demo_data.py
heroku run python scripts/generate_embeddings.py

# Monitor
heroku logs --tail
heroku ps
heroku open
```

---

**Happy deploying! 🎮🚀**

**Last Updated:** December 16, 2025
