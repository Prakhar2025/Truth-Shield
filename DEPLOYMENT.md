# Deployment Guide for Truth Shield

This guide covers deploying Truth Shield to production environments.

## Table of Contents

1. [Local Deployment](#local-deployment)
2. [Cloud Deployment](#cloud-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Production Checklist](#production-checklist)

## Local Deployment

### Windows

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### macOS/Linux

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Cloud Deployment

### Heroku Deployment

1. **Create Procfile:**
```
web: gunicorn app:app
```

2. **Create runtime.txt:**
```
python-3.9.0
```

3. **Update requirements.txt:**
```bash
pip install gunicorn
pip freeze > requirements.txt
```

4. **Deploy:**
```bash
heroku login
heroku create your-app-name
git push heroku main
```

### AWS Deployment

1. **Using Elastic Beanstalk:**
```bash
pip install awsebcli
eb init -p python-3.9 truth-shield
eb create truth-shield-env
eb deploy
```

2. **Using EC2:**
   - Launch EC2 instance (Ubuntu 20.04)
   - Install Python 3.9 and pip
   - Clone repository
   - Setup virtual environment
   - Configure Nginx as reverse proxy
   - Use Gunicorn to run Flask app

### Google Cloud Deployment

1. **Using App Engine:**
```bash
gcloud app deploy
```

2. **Using Cloud Run:**
```bash
gcloud run deploy truth-shield \
  --source . \
  --platform managed \
  --region us-central1
```

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Build and Run

```bash
# Build image
docker build -t truth-shield:latest .

# Run container
docker run -p 5000:5000 truth-shield:latest
```

### Docker Compose

```yaml
version: '3'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./static:/app/static
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
```

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Configure a reverse proxy (Nginx, Apache)
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper logging
- [ ] Set up monitoring and alerts
- [ ] Configure backups for logs and uploads
- [ ] Set resource limits
- [ ] Configure auto-scaling if needed
- [ ] Set up CI/CD pipeline
- [ ] Test all endpoints thoroughly
- [ ] Configure rate limiting
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure CDN for static files
- [ ] Set up database backups (if applicable)

## Environment Variables

```env
FLASK_ENV=production
FLASK_DEBUG=False
MAX_CONTENT_LENGTH=500000000
UPLOAD_FOLDER=/var/uploads
LOGS_FOLDER=/var/logs
```

## Performance Optimization

1. **Enable Caching:**
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

2. **Use CDN for static files**

3. **Implement rate limiting:**
```python
from flask_limiter import Limiter

limiter = Limiter(app)
```

4. **Configure Gzip compression:**
```python
from flask_compress import Compress

Compress(app)
```

## Monitoring

### Log Monitoring

```bash
# Check application logs
tail -f logs/app.log

# Monitor system resources
top
```

### Health Checks

```python
@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy'}, 200
```

## Troubleshooting

### High Memory Usage

- Reduce model batch size
- Implement request queuing
- Use process limits with gunicorn: `gunicorn -w 4 --max-requests 1000`

### Slow Response Times

- Check model loading time
- Implement caching
- Use GPU acceleration if available
- Increase number of workers

### Model Loading Issues

- Ensure model files are present
- Check file permissions
- Verify TensorFlow version compatibility

## Rollback Procedures

```bash
# Git rollback
git revert <commit-hash>
git push

# Docker rollback
docker run -p 5000:5000 truth-shield:previous-tag
```
