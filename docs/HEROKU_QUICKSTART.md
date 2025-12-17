# Heroku Deployment - Quick Reference

Cheat sheet untuk deploy BIG GAMES Backend ke Heroku via GitHub.

---

## Step-by-Step

### 1. Heroku Setup (One-time)

```bash
# Login ke Heroku Dashboard
https://dashboard.heroku.com

# Create New App
App Name: biggames-backend
Region: United States

# Add Heroku Postgres
Resources → Add-ons → Heroku Postgres → Essential 0 (Free)
```

### 2. GitHub Connection

```bash
Deploy → Deployment method → GitHub
Connect to: your-username/biggames_backend
Branch: main
Enable Automatic Deploys
```

### 3. Environment Variables

```bash
Settings → Config Vars → Reveal Config Vars
```

Add:

```env
JWT_SECRET_KEY=<generate-random-32-chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BANK_ACCOUNT_NAME=PT BIG GAMES INDONESIA
BANK_ACCOUNT_NUMBER=1234567890
BANK_NAME=BCA
QRIS_IMAGE_URL=https://your-storage.com/qris.png
```

### 4. Enable pgvector

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login & enable extension
heroku login
heroku pg:psql -a biggames-backend
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### 5. Deploy

```bash
Deploy → Manual Deploy → Deploy Branch
```

### 6. Seed Data

```bash
heroku run python scripts/seed_demo_data.py -a biggames-backend
```

---

## Automatic Deployment

After setup:

```bash
# Any push to main branch
git add .
git commit -m "Update feature"
git push origin main

# Heroku auto-deploys!
```

---

## Essential Commands

```bash
# View logs
heroku logs --tail -a biggames-backend

# Restart app
heroku restart -a biggames-backend

# Run command
heroku run <command> -a biggames-backend

# Database console
heroku pg:psql -a biggames-backend

# Check app status
heroku ps -a biggames-backend

# Open app
heroku open -a biggames-backend
```

---

## URLs

- Dashboard: https://dashboard.heroku.com/apps/biggames-backend
- App: https://biggames-backend.herokuapp.com
- API Docs: https://biggames-backend.herokuapp.com/docs
- Health: https://biggames-backend.herokuapp.com/health

---

## Troubleshooting

### Build Failed

```bash
heroku logs --tail -a biggames-backend
```

### App Crashed

```bash
heroku restart -a biggames-backend
heroku ps:scale web=1 -a biggames-backend
```

### Database Issues

```bash
heroku pg:info -a biggames-backend
heroku pg:reset -a biggames-backend
```

### Migration Failed

```bash
heroku run alembic upgrade head -a biggames-backend
```

---

## Keep App Awake (Free Tier)

Use UptimeRobot:

```
URL: https://biggames-backend.herokuapp.com/health
Interval: 5 minutes
```

---

## Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Cost

**Free Tier:**

- Dyno: 550 hours/month (1000 with verified credit card)
- Database: 1GB storage, 20 connections
- Sleeps after 30 mins inactivity

**Hobby Tier ($7/month):**

- No sleeping
- Better performance
- Custom domain SSL

---

## Full Documentation

See: [DEPLOY_HEROKU_GITHUB.md](DEPLOY_HEROKU_GITHUB.md)
