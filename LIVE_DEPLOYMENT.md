# 🌐 Truth Shield - Live Website Deployment Guide

## Quick Deployment Options

### 🟢 Option 1: Heroku (Fastest & Free)

#### Step 1: Install Heroku CLI
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2: Login to Heroku
```bash
heroku login
```

#### Step 3: Create Procfile in project root
```bash
echo "web: gunicorn app:app" > Procfile
```

#### Step 4: Deploy
```bash
cd "c:\Users\prakh\OneDrive\Desktop\Desktop\combine wala\combine wala"
heroku create truth-shield
git push heroku main
```

#### Step 5: Open live website
```bash
heroku open
```

**Live URL:** `https://truth-shield.herokuapp.com`

---

### 🔵 Option 2: Railway.app (Modern & Easy)

#### Step 1: Go to https://railway.app
#### Step 2: Sign up with GitHub
#### Step 3: Create new project → GitHub repo
#### Step 4: Connect your repository
#### Step 5: Add environment variables
- Set `FLASK_ENV=production`
- Set `FLASK_DEBUG=False`

#### Step 6: Deploy automatically

**Live URL:** Provided by Railway

---

### 🟠 Option 3: Render (Simple Deployment)

#### Step 1: Go to https://render.com
#### Step 2: Sign up with GitHub
#### Step 3: New → Web Service
#### Step 4: Connect GitHub repo (Truth-Shield)
#### Step 5: Configure:
- **Name:** truth-shield
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

#### Step 6: Deploy

**Live URL:** Provided by Render

---

### 🟡 Option 4: Google Cloud Run

#### Step 1: Create Dockerfile (if not exists)

Create `Dockerfile` in project root:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "--workers", "2", "app:app"]
```

#### Step 2: Deploy
```bash
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
gcloud run deploy truth-shield --source . --platform managed --region us-central1 --allow-unauthenticated
```

**Live URL:** Provided by Google Cloud

---

### 🔴 Option 5: AWS (Production-Grade)

#### Using Elastic Beanstalk:
```bash
pip install awsebcli
eb init -p python-3.9 truth-shield
eb create truth-shield-env
eb deploy
```

#### Using EC2 + Gunicorn + Nginx:
See detailed instructions in `DEPLOYMENT.md`

---

## ⚡ Quick Start Comparison

| Platform | Cost | Setup Time | Scale | Best For |
|----------|------|-----------|-------|----------|
| **Heroku** | $7-50/month | 5 min | Small-Medium | Prototypes, demos |
| **Railway** | $5+/month | 5 min | Small-Medium | Startups |
| **Render** | Free-$20/month | 5 min | Small-Medium | Portfolio projects |
| **Google Cloud Run** | $0.20-0.80/req | 10 min | Medium-Large | Enterprise |
| **AWS** | $5-200+/month | 30 min | Large | Production |

---

## 📋 Pre-Deployment Checklist

- [ ] Update email in README.md
- [ ] Add models to project (or external link)
- [ ] Test locally: `python app.py`
- [ ] Check `.gitignore` is working
- [ ] Verify `requirements.txt` versions
- [ ] Update `DEPLOYMENT_URL` in README

---

## 🚀 Model Files Handling for Live Deployment

Since `.h5` files are large and excluded from git:

### Option A: GitHub Releases
```bash
# Create release with model files attached
gh release create v1.0.0 --title "Truth Shield v1.0.0"
# Upload model/*.h5 files manually in GitHub UI
```

### Option B: External Storage
1. Upload models to Google Drive
2. Update app.py to download on startup:
```python
import gdown

def download_models():
    if not os.path.exists('model/new_xception.h5'):
        gdown.download('GOOGLE_DRIVE_ID', 'model/new_xception.h5')
        
download_models()
```

### Option C: Cloud Storage
1. Upload to AWS S3, Google Cloud Storage, or Azure Blob Storage
2. Download during app startup

---

## 🔗 After Deployment - Update README

Add to your README.md:

```markdown
## 🌐 Live Demo

[![Deploy Status](https://img.shields.io/badge/Status-Live-brightgreen.svg)](YOUR_LIVE_URL)

**🔗 Live Website:** [Truth Shield - Deepfake Detection](YOUR_LIVE_URL)

- **Image Detection:** Analyze images for deepfakes
- **Video Detection:** Frame-by-frame video analysis
- **Real-time Confidence:** Get accuracy scores for all predictions

> Note: First request may take 10-15 seconds as models load. Subsequent requests are faster.

### Quick Links:
- [Live Application](YOUR_LIVE_URL)
- [GitHub Repository](https://github.com/Prakhar2025/Truth-Shield)
- [Documentation](https://github.com/Prakhar2025/Truth-Shield/blob/main/README.md)
- [Report Issues](https://github.com/Prakhar2025/Truth-Shield/issues)
```

---

## 📊 Live Deployment URLs

Once deployed, add these to your profile:

```markdown
## Deployed Applications

| Application | Platform | URL | Status |
|-------------|----------|-----|--------|
| Truth Shield | [Heroku/Railway/Render] | [Your URL] | ✅ Live |
```

---

## 🆘 Common Deployment Issues & Fixes

### Issue: Models Not Found
**Solution:**
```python
# Add to app.py before loading models
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress warnings
```

### Issue: Memory Exceeded
**Solution:**
```python
# Reduce model size in app.py
# Use model quantization or smaller architecture
```

### Issue: Timeout on Large Videos
**Solution:**
```python
# In deployment config, increase timeout:
# Heroku: Add to Procfile: `--timeout 120`
# Google Cloud Run: Set timeout to 3600s in yaml
```

### Issue: Uploads Directory Not Writable
**Solution:**
```python
# Use /tmp for Heroku/Cloud Run:
UPLOAD_FOLDER = '/tmp/uploads'
```

---

## 📈 Monitoring Live Application

### Heroku Logs:
```bash
heroku logs --tail
```

### View Model Performance:
```bash
# Check predictions.json in logs/
tail -f logs/predictions.json
```

---

## 💰 Cost Estimation (Monthly)

| Platform | Free Tier | Paid Entry | Production |
|----------|-----------|-----------|-----------|
| Heroku | ❌ | $7 | $50+ |
| Railway | ✅ $5 free | $5+ | $50+ |
| Render | ✅ Free | $7+ | $50+ |
| Google Cloud Run | ✅ (limits) | Variable | $100+ |
| AWS | Depends | $20+ | $100+ |

---

## 🎯 Recommended Approach

**For Quick Demo:** Railway or Render (5 minutes)  
**For Portfolio:** Render or Heroku (10 minutes)  
**For Production:** AWS or Google Cloud (30 minutes)

---

## 📞 Need Help?

- Check `DEPLOYMENT.md` for detailed guides
- Review `CONTRIBUTING.md` for development setup
- Open issue on GitHub for support

---

**Good Luck! 🚀**

Your Truth Shield application is ready to go live!

*Note: Update this file with your actual deployment URL once live.*
