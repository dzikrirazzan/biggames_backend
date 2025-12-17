# Deploy ke Heroku via GitHub Integration

Panduan lengkap deploy BIG GAMES Backend ke Heroku menggunakan GitHub automatic deployment.

---

## Prerequisites

- Akun Heroku (https://heroku.com)
- Repository sudah di push ke GitHub
- Heroku CLI (optional, untuk troubleshooting)

---

## Langkah 1: Persiapan Repository

### 1.1 Pastikan File-File Berikut Ada

**Procfile**

```
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**runtime.txt**

```
python-3.11.0
```

**requirements.txt**

- Sudah lengkap dengan semua dependencies

### 1.2 Push ke GitHub

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push origin main
```

---

## Langkah 2: Setup Heroku Project

### 2.1 Login ke Heroku

1. Buka https://dashboard.heroku.com
2. Login dengan akun Heroku kamu

### 2.2 Create New App

1. Klik **"New"** di pojok kanan atas
2. Pilih **"Create new app"**
3. Isi:
   - App name: `biggames-backend` (atau nama lain yang available)
   - Region: **United States** atau **Europe** (pilih yang terdekat)
4. Klik **"Create app"**

---

## Langkah 3: Setup PostgreSQL Database

### 3.1 Add Heroku Postgres

1. Di dashboard app, pergi ke tab **"Resources"**
2. Di bagian **"Add-ons"**, search: `Heroku Postgres`
3. Pilih **"Heroku Postgres"**
4. Plan: **Essential 0** (gratis untuk development)
5. Klik **"Submit Order Form"**

### 3.2 Verify Database

1. Klik addon **"Heroku Postgres"**
2. Akan muncul database credentials
3. Copy **DATABASE_URL** (akan otomatis tersedia sebagai environment variable)

---

## Langkah 4: Connect ke GitHub

### 4.1 Link GitHub Repository

1. Di dashboard app, pergi ke tab **"Deploy"**
2. Di bagian **"Deployment method"**, pilih **GitHub**
3. Klik **"Connect to GitHub"**
4. Authorize Heroku untuk akses GitHub (jika belum)
5. Search repository: `biggames_backend`
6. Klik **"Connect"**

### 4.2 Enable Automatic Deploys

1. Scroll ke bagian **"Automatic deploys"**
2. Pilih branch: **main** (atau branch yang kamu gunakan)
3. Centang **"Wait for CI to pass before deploy"** (optional)
4. Klik **"Enable Automatic Deploys"**

### 4.3 Manual Deploy (Pertama Kali)

1. Scroll ke bagian **"Manual deploy"**
2. Pilih branch: **main**
3. Klik **"Deploy Branch"**
4. Tunggu proses build selesai (sekitar 5-10 menit)

---

## Langkah 5: Configure Environment Variables

### 5.1 Set Config Vars

1. Pergi ke tab **"Settings"**
2. Klik **"Reveal Config Vars"**
3. Tambahkan variables berikut:

| Key                           | Value                                 | Keterangan             |
| ----------------------------- | ------------------------------------- | ---------------------- |
| `DATABASE_URL`                | (Sudah otomatis dari Heroku Postgres) | URL PostgreSQL         |
| `JWT_SECRET_KEY`              | `your-super-secret-key-min-32-chars`  | Generate random string |
| `JWT_ALGORITHM`               | `HS256`                               | Algoritma JWT          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                  | Durasi token           |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                   | Durasi refresh token   |
| `BANK_ACCOUNT_NAME`           | `PT BIG GAMES INDONESIA`              | Nama rekening          |
| `BANK_ACCOUNT_NUMBER`         | `1234567890`                          | Nomor rekening         |
| `BANK_NAME`                   | `BCA`                                 | Nama bank              |
| `QRIS_IMAGE_URL`              | `https://your-storage.com/qris.png`   | URL QRIS image         |

### 5.2 Generate JWT Secret Key

```bash
# Cara 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Cara 2: OpenSSL
openssl rand -base64 32

# Cara 3: Online
# https://generate-secret.vercel.app/32
```

### 5.3 Optional: OpenAI API Key

Jika ingin pakai OpenAI embeddings (default pakai Hugging Face):

| Key              | Value    |
| ---------------- | -------- |
| `OPENAI_API_KEY` | `sk-...` |

---

## Langkah 6: Setup pgvector Extension

### 6.1 Enable pgvector via Heroku CLI

**Install Heroku CLI** (jika belum):

```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Download dari: https://devcenter.heroku.com/articles/heroku-cli

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

**Login dan Enable Extension:**

```bash
# Login
heroku login

# Connect ke app
heroku apps:info -a biggames-backend

# Enable pgvector
heroku pg:psql -a biggames-backend
```

Di PostgreSQL console:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### 6.2 Alternative: Via Heroku Dashboard

1. Klik addon **"Heroku Postgres"**
2. Pergi ke tab **"Dataclips"** atau **"Settings"**
3. Jalankan SQL query:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## Langkah 7: Run Database Migrations

Migrations akan otomatis jalan via Procfile (`alembic upgrade head`), tapi bisa manual via:

```bash
heroku run alembic upgrade head -a biggames-backend
```

---

## Langkah 8: Seed Demo Data (Optional)

```bash
heroku run python scripts/seed_demo_data.py -a biggames-backend
```

---

## Langkah 9: Verify Deployment

### 9.1 Check Application Logs

```bash
heroku logs --tail -a biggames-backend
```

Atau via dashboard:

1. Tab **"More"** → **"View logs"**

### 9.2 Test API Endpoints

**Get App URL:**

```bash
heroku apps:info -a biggames-backend | grep "Web URL"
```

Atau buka: https://biggames-backend.herokuapp.com

**Test Health Check:**

```bash
curl https://biggames-backend.herokuapp.com/health
```

**Expected Response:**

```json
{
  "status": "healthy"
}
```

**Test API Docs:**

Browser: https://biggames-backend.herokuapp.com/docs

### 9.3 Test Authentication

```bash
curl -X POST https://biggames-backend.herokuapp.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@biggames.com",
    "password": "admin123"
  }'
```

---

## Langkah 10: Setup Custom Domain (Optional)

### 10.1 Add Custom Domain

```bash
heroku domains:add api.biggames.id -a biggames-backend
```

### 10.2 Configure DNS

Add CNAME record di DNS provider:

```
Type: CNAME
Name: api
Value: biggames-backend.herokuapp.com
```

### 10.3 Enable SSL

```bash
heroku certs:auto:enable -a biggames-backend
```

---

## Automatic Deployment Flow

Setelah setup, workflow otomatis:

```
1. Push code ke GitHub
   git push origin main

2. Heroku detect perubahan

3. Automatic build & deploy
   - Install dependencies
   - Run Procfile commands
   - Start application

4. App live dengan code terbaru
```

---

## Troubleshooting

### Issue 1: Build Failed

**Check Logs:**

```bash
heroku logs --tail -a biggames-backend
```

**Common Issues:**

- Python version tidak support: Update `runtime.txt`
- Dependencies error: Check `requirements.txt`
- Procfile salah format: Pastikan no trailing spaces

### Issue 2: Database Connection Error

**Check DATABASE_URL:**

```bash
heroku config:get DATABASE_URL -a biggames-backend
```

**Reset Connection Pool:**

```bash
heroku pg:reset -a biggames-backend
```

### Issue 3: Application Crashes

**Check Dyno Status:**

```bash
heroku ps -a biggames-backend
```

**Restart Dyno:**

```bash
heroku restart -a biggames-backend
```

**Scale Dyno:**

```bash
heroku ps:scale web=1 -a biggames-backend
```

### Issue 4: Migrations Failed

**Run Manually:**

```bash
heroku run alembic upgrade head -a biggames-backend
```

**Check Migration Status:**

```bash
heroku run alembic current -a biggames-backend
```

### Issue 5: pgvector Not Found

**Enable Extension:**

```bash
heroku pg:psql -a biggames-backend
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

## Monitoring & Maintenance

### View Application Metrics

```bash
heroku metrics -a biggames-backend
```

Atau via dashboard: Tab **"Metrics"**

### View Database Stats

```bash
heroku pg:info -a biggames-backend
```

### View Active Connections

```bash
heroku pg:ps -a biggames-backend
```

### Backup Database

**Manual Backup:**

```bash
heroku pg:backups:capture -a biggames-backend
```

**Schedule Automatic Backups:**

```bash
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Los_Angeles' -a biggames-backend
```

### Download Backup

```bash
heroku pg:backups:download -a biggames-backend
```

---

## Cost Optimization

### Free Tier Limits

**Heroku Free Dyno:**

- 550 dyno hours/month (tanpa credit card)
- 1000 dyno hours/month (dengan credit card verified)
- Sleeps after 30 minutes inactivity

**Heroku Postgres Essential 0:**

- 1 GB storage
- 20 connections max
- No automatic backups

### Keep App Awake

**Option 1: Cron Job**

Gunakan service seperti cron-job.org untuk ping app setiap 25 menit:

```
URL: https://biggames-backend.herokuapp.com/health
Interval: Every 25 minutes
```

**Option 2: UptimeRobot**

1. Sign up di https://uptimerobot.com
2. Add New Monitor
3. URL: https://biggames-backend.herokuapp.com/health
4. Interval: 5 minutes (free)

### Upgrade to Hobby Dyno

Untuk production, upgrade ke Hobby ($7/month):

```bash
heroku ps:type hobby -a biggames-backend
```

Benefits:

- No sleeping
- Better performance
- Custom domain SSL

---

## Scaling

### Horizontal Scaling

Add more dynos:

```bash
heroku ps:scale web=2 -a biggames-backend
```

### Vertical Scaling

Upgrade dyno type:

```bash
heroku ps:type performance-m -a biggames-backend
```

### Database Scaling

Upgrade plan:

```bash
heroku addons:upgrade heroku-postgresql:standard-0 -a biggames-backend
```

---

## CI/CD Integration

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "biggames-backend"
          heroku_email: "your-email@example.com"
```

---

## Best Practices

### 1. Environment-Specific Settings

Gunakan Heroku config vars untuk production values:

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Heroku sets DATABASE_URL automatically
    database_url: str = Field(..., env="DATABASE_URL")

    # Override for production
    debug: bool = Field(default=False, env="DEBUG")
```

### 2. Logging

Heroku automatically captures stdout/stderr:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. Health Checks

Implementasi health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
```

### 4. Graceful Shutdown

Heroku sends SIGTERM sebelum kill:

```python
import signal
import sys

def signal_handler(sig, frame):
    logging.info("Graceful shutdown...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
```

---

## Security Checklist

- [ ] JWT_SECRET_KEY menggunakan random string minimal 32 characters
- [ ] DEBUG mode = False di production
- [ ] Database credentials secure (via Heroku config vars)
- [ ] CORS configured untuk domain frontend only
- [ ] Rate limiting enabled
- [ ] HTTPS enforced (automatic via Heroku)
- [ ] Sensitive data tidak di commit ke GitHub
- [ ] .env file in .gitignore

---

## Quick Reference

### Useful Commands

```bash
# View logs
heroku logs --tail -a biggames-backend

# Restart app
heroku restart -a biggames-backend

# Run migrations
heroku run alembic upgrade head -a biggames-backend

# Open app in browser
heroku open -a biggames-backend

# Check dyno status
heroku ps -a biggames-backend

# Database console
heroku pg:psql -a biggames-backend

# View config vars
heroku config -a biggames-backend

# Set config var
heroku config:set KEY=VALUE -a biggames-backend

# Scale dynos
heroku ps:scale web=1 -a biggames-backend
```

### Important URLs

- Dashboard: https://dashboard.heroku.com/apps/biggames-backend
- App URL: https://biggames-backend.herokuapp.com
- API Docs: https://biggames-backend.herokuapp.com/docs
- Logs: https://dashboard.heroku.com/apps/biggames-backend/logs

---

## Summary

**Setup Steps:**

1. Create Heroku app
2. Add Heroku Postgres
3. Connect GitHub repository
4. Enable automatic deploys
5. Configure environment variables
6. Enable pgvector extension
7. Deploy branch
8. Verify deployment

**Automatic Workflow:**

```
Push to GitHub → Heroku Builds → Auto Deploy → App Live
```

**Monitoring:**

- Heroku Dashboard
- Application logs
- Database metrics
- UptimeRobot alerts

Deployment selesai! Setiap kali push ke branch main, Heroku akan otomatis build dan deploy.
