# Deploy ke Heroku + Supabase

Panduan deploy BIG GAMES Backend menggunakan:

- **Heroku Student Account** untuk backend API
- **Supabase Free Account** untuk PostgreSQL database

---

## Kenapa Heroku + Supabase?

**Heroku Student Benefits:**

- $13/month credits (cukup untuk Hobby dyno)
- No credit card required
- GitHub Student Pack perks

**Supabase Free Tier:**

- 500 MB database storage
- Unlimited API requests
- pgvector extension included
- Automatic backups
- Dashboard yang mudah

---

## Prerequisites

- GitHub Student Pack (https://education.github.com/pack)
- Akun Heroku (linked dengan GitHub Student)
- Akun Supabase (free)
- Repository sudah di GitHub

---

## Part 1: Setup Supabase Database

### 1.1 Create Supabase Account

1. Buka https://supabase.com
2. Click **"Start your project"**
3. Sign up dengan GitHub account
4. Verify email

### 1.2 Create New Project

1. Click **"New Project"**
2. Isi form:
   - **Name**: `biggames-backend`
   - **Database Password**: Buat strong password (save ini!)
   - **Region**: Southeast Asia (Singapore) - terdekat dengan Indonesia
   - **Pricing Plan**: Free
3. Click **"Create new project"**
4. Tunggu ~2 menit (project setup)

### 1.3 Enable pgvector Extension

1. Di dashboard Supabase, sidebar kiri → **"Database"**
2. Click tab **"Extensions"**
3. Search: `vector`
4. Enable **"vector"** extension
5. Status harus jadi "Enabled"

### 1.4 Get Database Connection String

1. Sidebar → **"Project Settings"** (icon gear)
2. Click **"Database"** di menu kiri
3. Scroll ke **"Connection string"**
4. Copy **"URI"** mode (bukan Transaction/Session)
5. Format: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`

**Penting:** Replace `[YOUR-PASSWORD]` dengan password yang tadi kamu buat!

**Connection Pooling (Recommended):**

- Untuk production, gunakan **"Connection pooling"** → **"Transaction mode"**
- Format: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true`
- Port 6543 (bukan 5432)

---

## Part 2: Setup Heroku

### 2.1 Verify GitHub Student Pack

1. Buka https://education.github.com/pack
2. Apply for Student Pack (jika belum)
3. Verify dengan email .edu atau student ID
4. Dapat $13/month Heroku credits

### 2.2 Connect Heroku dengan GitHub Student

1. Buka https://www.heroku.com/github-students
2. Click **"Get the student offer"**
3. Login/Sign up Heroku
4. Verify dengan GitHub Student Pack

### 2.3 Create Heroku App

1. Buka https://dashboard.heroku.com
2. Click **"New"** → **"Create new app"**
3. Isi:
   - **App name**: `biggames-backend` (atau nama lain)
   - **Region**: United States (atau Europe)
4. Click **"Create app"**

---

## Part 3: Connect GitHub to Heroku

### 3.1 Link Repository

1. Di dashboard app Heroku, tab **"Deploy"**
2. **Deployment method** → Click **"GitHub"**
3. Click **"Connect to GitHub"**
4. Authorize Heroku (jika diminta)
5. Search repository: `biggames_backend`
6. Click **"Connect"**

### 3.2 Enable Automatic Deploys

1. Scroll ke **"Automatic deploys"**
2. Choose branch: **main**
3. Optional: Check **"Wait for CI to pass before deploy"**
4. Click **"Enable Automatic Deploys"**

---

## Part 4: Configure Environment Variables

### 4.1 Set Config Vars

1. Tab **"Settings"**
2. Click **"Reveal Config Vars"**
3. Add variables satu per satu:

**Database (Supabase):**

| Key            | Value                      | Contoh                                                                                |
| -------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| `DATABASE_URL` | Supabase URI dari Part 1.4 | `postgresql://postgres:your-password@db.xxx.supabase.co:6543/postgres?pgbouncer=true` |

**JWT Authentication:**

| Key                           | Value                                 |
| ----------------------------- | ------------------------------------- |
| `JWT_SECRET_KEY`              | Generate random (lihat cara di bawah) |
| `JWT_ALGORITHM`               | `HS256`                               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                  |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                   |

**Payment Info:**

| Key                   | Value                           |
| --------------------- | ------------------------------- |
| `BANK_ACCOUNT_NAME`   | `PT BIG GAMES INDONESIA`        |
| `BANK_ACCOUNT_NUMBER` | `1234567890`                    |
| `BANK_NAME`           | `BCA`                           |
| `QRIS_IMAGE_URL`      | `https://your-cdn.com/qris.png` |

**Optional - OpenAI:**

| Key              | Value                                                   |
| ---------------- | ------------------------------------------------------- |
| `OPENAI_API_KEY` | `sk-...` (jika pakai OpenAI, default pakai HuggingFace) |

### 4.2 Generate JWT Secret Key

**Cara 1: Python**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Cara 2: OpenSSL**

```bash
openssl rand -base64 32
```

**Cara 3: Online**

```
https://generate-secret.vercel.app/32
```

Copy hasil dan paste ke `JWT_SECRET_KEY`

---

## Part 5: Deploy!

### 5.1 Manual Deploy (First Time)

1. Tab **"Deploy"**
2. Scroll ke **"Manual deploy"**
3. Choose branch: **main**
4. Click **"Deploy Branch"**
5. Tunggu build process (~5-10 menit)
6. Lihat logs real-time

### 5.2 Check Build Logs

Pastikan tidak ada error:

```
-----> Building on the Heroku-22 stack
-----> Using buildpack: heroku/python
-----> Python app detected
-----> Installing python-3.11.0
-----> Installing dependencies
-----> Installing requirements with pip
...
-----> Discovering process types
       Procfile declares types -> web
-----> Compressing...
-----> Launching...
       Released v1
       https://biggames-backend.herokuapp.com/ deployed to Heroku
```

### 5.3 Verify Deployment

**Check App Status:**

```bash
heroku apps:info -a biggames-backend
```

**View Logs:**

```bash
heroku logs --tail -a biggames-backend
```

**Test Health Endpoint:**

```bash
curl https://biggames-backend.herokuapp.com/health
```

Expected:

```json
{
  "status": "healthy"
}
```

---

## Part 6: Database Initialization

### 6.1 Run Migrations

Migrations akan otomatis jalan via Procfile saat deploy, tapi bisa manual juga:

**Option A: Via Heroku Web Console (Recommended untuk pemula)**

1. Buka https://dashboard.heroku.com/apps/biggames-backend
2. Klik **"More"** (pojok kanan atas) → **"Run console"**
3. Di popup terminal, ketik:
   ```bash
   alembic upgrade head
   ```
4. Tekan Enter dan tunggu selesai
5. Akan muncul output migration yang berhasil

**Option B: Via Terminal Lokal (Perlu Heroku CLI)**

Install Heroku CLI dulu (one-time):

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows - download installer
# https://devcenter.heroku.com/articles/heroku-cli

# Verify
heroku --version
```

Login & run migration:

```bash
heroku login
heroku run alembic upgrade head -a biggames-backend
```

### 6.2 Verify Tables Created

**Via Supabase Dashboard:**

1. Supabase dashboard → **"Table Editor"**
2. Cek tables: `users`, `rooms`, `reservations`, dll

**Via Heroku CLI:**

```bash
heroku run python -c "from app.db.session import engine; import asyncio; asyncio.run(engine.connect())" -a biggames-backend
```

### 6.3 Seed Demo Data

```bash
heroku run python scripts/seed_demo_data.py -a biggames-backend
```

Tunggu selesai (~1-2 menit)

---

## Part 7: Test API

### 7.1 Get App URL

```bash
heroku apps:info -a biggames-backend | grep "Web URL"
```

Atau: `https://biggames-backend.herokuapp.com`

### 7.2 Test API Docs

Browser: `https://biggames-backend.herokuapp.com/docs`

### 7.3 Test Login

```bash
curl -X POST https://biggames-backend.herokuapp.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@biggames.com",
    "password": "admin123"
  }'
```

Should return:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 7.4 Test Rooms Endpoint

```bash
curl https://biggames-backend.herokuapp.com/api/rooms
```

---

## Part 8: Automatic Deployment

### 8.1 Workflow

Setiap push ke GitHub main branch:

```bash
# Make changes
git add .
git commit -m "Add new feature"
git push origin main

# Heroku automatically:
# 1. Detects push
# 2. Builds app
# 3. Runs migrations (via Procfile)
# 4. Deploys to production
```

### 8.2 Monitor Deployment

**Via Heroku Dashboard:**

- Tab "Activity" → See deployment history

**Via CLI:**

```bash
heroku releases -a biggames-backend
```

---

## Monitoring & Management

### Heroku Commands

**View logs:**

```bash
heroku logs --tail -a biggames-backend
```

**Restart app:**

```bash
heroku restart -a biggames-backend
```

**Check dyno status:**

```bash
heroku ps -a biggames-backend
```

**Run command:**

```bash
heroku run <command> -a biggames-backend
```

**Open app:**

```bash
heroku open -a biggames-backend
```

### Supabase Dashboard

**Monitor Database:**

1. Dashboard → **"Database"**
2. View tables, run queries
3. Check storage usage

**View Logs:**

1. Dashboard → **"Logs"**
2. Real-time query logs

**API Usage:**

1. Dashboard → **"Settings"** → **"API"**
2. Monitor request count

---

## Database Management

### Backup Database

**Via Supabase (Automatic):**

- Free tier: Daily backups (7 days retention)
- Dashboard → **"Database"** → **"Backups"**

**Manual Backup:**

```bash
# Install Supabase CLI
npm install -g supabase

# Export database
supabase db dump -f backup.sql
```

**Via pg_dump:**

```bash
pg_dump "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" > backup.sql
```

### Restore Database

```bash
psql "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" < backup.sql
```

---

## Resource Limits

### Heroku Student Account

**Credits:**

- $13/month (dari GitHub Student Pack)
- Berlaku selama status student aktif

**Hobby Dyno ($7/month):**

- 512 MB RAM
- No sleeping
- Custom domain
- SSL included
- Metrics dashboard

**With $13 credits:**

- 1 Hobby dyno ($7) + 1 Mini Postgres ($5) = $12/month
- Atau 1 Hobby dyno ($7) + Supabase free = $7/month (lebih hemat!)

### Supabase Free Tier

**Database:**

- 500 MB storage
- Unlimited API requests
- 2 GB bandwidth
- Up to 500 MB file uploads
- 50 MB file upload size limit

**Limits:**

- Max 2 active projects
- 7 days log retention
- Daily backups (7 days)
- No point-in-time recovery

**When to Upgrade:**

- Database > 500 MB → Pro ($25/month)
- Need more projects → Pro
- Need longer log retention → Pro

---

## Cost Breakdown

### Current Setup (FREE!)

| Service   | Plan                 | Cost                             |
| --------- | -------------------- | -------------------------------- |
| Heroku    | Student (Hobby dyno) | $7/month (covered by $13 credit) |
| Supabase  | Free                 | $0                               |
| **Total** |                      | **$0** (with student credits)    |

### Scaling Options

**When Student Credits Expire:**

1. Downgrade to Heroku Eco ($5/month) + Supabase Free = $5/month
2. Or migrate to other platforms (Render, Railway, etc)

---

## Troubleshooting

### Issue 1: Slug Size Too Large (PALING UMUM!)

**Error:**

```
Compiled slug size: 2.8G is too large (max is 500M).
Push failed
```

**Penyebab:** PyTorch dengan CUDA libraries terlalu besar (~2.8 GB).

**Solusi:** Gunakan PyTorch **CPU-only** version (hemat 2.7 GB!).

**Sudah diperbaiki di `requirements.txt`:**

```python
# File requirements.txt sekarang pakai CPU-only:
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.2.0+cpu
```

**Commit & Deploy:**

```bash
git add requirements.txt .python-version
git commit -m "Use PyTorch CPU-only + .python-version"
git push origin main
```

**Build akan berhasil sekarang dengan slug size ~300 MB!**

**Note:** Heroku tidak punya GPU, jadi CPU-only version sudah cukup untuk production.

---

### Issue 2: runtime.txt Deprecated

**Warning:**

```
The runtime.txt file is deprecated.
```

**Solusi:** Sudah diganti dengan `.python-version`

File `.python-version` sudah dibuat dengan content: `3.11`

**Optional - hapus runtime.txt:**

```bash
git rm runtime.txt
git commit -m "Remove deprecated runtime.txt"
git push origin main
```

---

### Issue 3: Build Failed

**Check Buildpack:**

```bash
heroku buildpacks -a biggames-backend
```

Should show: `heroku/python`

**Check Python Version:**

- File `runtime.txt` harus ada
- Content: `python-3.11.0`

**View Build Logs:**

```bash
heroku logs --tail -a biggames-backend | grep "Build"
```

### Issue 4: Database Connection Failed

**Test Connection String:**

```bash
heroku run python -c "import os; print(os.getenv('DATABASE_URL'))" -a biggames-backend
```

**Verify Supabase:**

- Dashboard → **"Settings"** → **"Database"**
- Connection pooler mode: **Transaction**
- Port: 6543 (not 5432)

**Check Firewall:**
Supabase allows all IPs by default, tapi bisa check:

- Dashboard → **"Settings"** → **"Database"** → **"Network restrictions"**

### Issue 5: pgvector Extension Not Found

**Enable via Supabase:**

```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

**Verify:**

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Issue 6: Migration Failed

**Run Manually:**

```bash
heroku run alembic upgrade head -a biggames-backend
```

**Check Current Version:**

```bash
heroku run alembic current -a biggames-backend
```

**View Migration History:**

```bash
heroku run alembic history -a biggames-backend
```

### Issue 7: App Crashes After Deploy

**Check Logs:**

```bash
heroku logs --tail -a biggames-backend
```

**Common Issues:**

- Missing environment variables
- Wrong DATABASE_URL format
- Dependencies not installed

**Restart:**

```bash
heroku restart -a biggames-backend
```

### Issue 9: Slow Performance

**Check Dyno Metrics:**

```bash
heroku ps -a biggames-backend
```

**Upgrade Dyno:**

```bash
# From Eco to Basic
heroku ps:type basic -a biggames-backend

# From Basic to Standard
heroku ps:type standard-1x -a biggames-backend
```

---

## Security Best Practices

### 1. Environment Variables

- Never commit `.env` to GitHub
- Use strong JWT_SECRET_KEY (min 32 chars)
- Rotate secrets regularly

### 2. Database

**Supabase Security:**

- Enable Row Level Security (RLS) if using Supabase API
- Restrict IP access jika perlu
- Use connection pooling for production

**Connection String:**

- Use transaction mode pooler (port 6543)
- Never expose in logs/code

### 3. API Security

- Enable rate limiting
- Use HTTPS only
- Validate all inputs
- Implement CORS properly

### 4. Heroku

- Enable automatic security updates
- Use Heroku metrics for monitoring
- Set up alerts for errors

---

## Monitoring & Alerts

### Heroku Metrics

```bash
heroku ps -a biggames-backend
```

Dashboard → **"Metrics"** tab:

- Response time
- Throughput
- Memory usage
- Error rate

### Supabase Monitoring

Dashboard → **"Reports"**:

- Database size
- API requests
- Query performance
- Connection count

### UptimeRobot (Free Monitoring)

1. Sign up: https://uptimerobot.com
2. Add monitor:
   - Type: HTTPS
   - URL: `https://biggames-backend.herokuapp.com/health`
   - Interval: 5 minutes
3. Get alerts via email/Slack

---

## Scaling Guide

### When to Scale?

**Indicators:**

- Response time > 2 seconds
- Memory usage > 80%
- Database connections maxed out
- 500 errors frequent

### Horizontal Scaling

**Add More Dynos:**

```bash
heroku ps:scale web=2 -a biggames-backend
```

Cost: 2x dyno price

### Vertical Scaling

**Upgrade Dyno Type:**

```bash
# Standard-1X (512 MB → 1 GB RAM)
heroku ps:type standard-1x -a biggames-backend

# Standard-2X (2 GB RAM)
heroku ps:type standard-2x -a biggames-backend
```

### Database Scaling

**Upgrade Supabase:**

- Free → Pro ($25/month)
- 8 GB storage
- 100 GB bandwidth
- Point-in-time recovery

---

## Migration Path

### When Student Credits End

**Option 1: Stay on Heroku**

- Downgrade to Eco dyno ($5/month)
- Keep Supabase free
- Total: $5/month

**Option 2: Move to Render**

- Free tier with 750 hours/month
- Keep Supabase
- Total: $0

**Option 3: Railway**

- $5 credit/month free
- Keep Supabase
- Total: $0 (with usage limits)

---

## Quick Command Reference

```bash
# View logs
heroku logs --tail -a biggames-backend

# Restart app
heroku restart -a biggames-backend

# Run migrations
heroku run alembic upgrade head -a biggames-backend

# Seed data
heroku run python scripts/seed_demo_data.py -a biggames-backend

# Check status
heroku ps -a biggames-backend

# View config
heroku config -a biggames-backend

# Set env var
heroku config:set KEY=VALUE -a biggames-backend

# Open app
heroku open -a biggames-backend

# Database console (via Supabase)
# Use Supabase dashboard SQL Editor
```

---

## Summary

**Setup Complete:**

1. Supabase database (500 MB free)
2. Heroku app (covered by student credits)
3. GitHub automatic deployment
4. pgvector extension enabled
5. All environment variables configured

**URLs:**

- App: https://biggames-backend.herokuapp.com
- API Docs: https://biggames-backend.herokuapp.com/docs
- Supabase: https://app.supabase.com

**Workflow:**

```
Push to GitHub main
    ↓
Heroku builds & deploys
    ↓
Connects to Supabase
    ↓
App live!
```

Selamat! Backend sudah production-ready dengan biaya $0 (selama masih student)!
