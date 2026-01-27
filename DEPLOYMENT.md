# 🌐 PDF to Audio Converter - Production Deployment Guide

A production-ready web application that converts PDF documents to audio files using text-to-speech technology.

## 🚀 Deployment Options

### Option 1: Docker (Recommended)

#### Quick Start with Docker
```bash
# Clone the repository
git clone <your-repo-url>
cd pdf-audio-converter

# Build and run with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:5000
```

#### With Nginx Reverse Proxy
```bash
# Run with Nginx (for production)
docker-compose --profile with-nginx up -d

# Access via Nginx
open http://localhost
```

### Option 2: Traditional Server Deployment

#### Prerequisites
- Python 3.11+
- Virtual environment
- System dependencies: `espeak`, `ffmpeg`, `portaudio19-dev`

#### Ubuntu/Debian Setup
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv build-essential \
    espeak espeak-data libespeak1 libespeak-dev \
    portaudio19-dev python3-dev ffmpeg

# Clone and setup
git clone <your-repo-url>
cd pdf-audio-converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# Configure environment
cp .env.example .env
# Edit .env with your production settings

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
```

### Option 3: Cloud Platform Deployment

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name

# Add buildpacks
heroku buildpacks:add --index 1 heroku-community/apt
heroku buildpacks:add --index 2 heroku/python

# Create Aptfile for system dependencies
echo "espeak espeak-data libespeak1 libespeak-dev portaudio19-dev ffmpeg" > Aptfile

# Set environment variables
heroku config:set SECRET_KEY="your-secure-secret-key"
heroku config:set FLASK_ENV=production

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Open app
heroku open
```

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
```

#### DigitalOcean App Platform
1. Create new app from GitHub repository
2. Set environment variables:
   - `SECRET_KEY`: Your secure secret key
   - `FLASK_ENV`: production
3. Deploy automatically

## ⚙️ Configuration

### Environment Variables

Create `.env` file:
```bash
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=production
PORT=5000
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=output
```

### Production Security Checklist

- ✅ Set secure `SECRET_KEY`
- ✅ Enable HTTPS with SSL certificates
- ✅ Configure rate limiting (included in nginx.conf)
- ✅ Set up file cleanup cron job
- ✅ Monitor logs and disk usage
- ✅ Configure firewall rules
- ✅ Regular security updates

## 🔧 Monitoring & Maintenance

### Health Check
```bash
curl http://your-domain.com/health
```

### Log Monitoring
```bash
# Docker logs
docker-compose logs -f pdf-audio-converter

# Traditional deployment
tail -f logs/pdf_audio_converter.log
```

### Cleanup Old Files
The application automatically cleans up files older than 1 hour. You can also trigger manual cleanup:
```bash
curl http://your-domain.com/cleanup
```

### Disk Usage Monitoring
```bash
# Monitor upload and output directories
du -sh uploads/ output/ logs/
```

## 🚨 Troubleshooting

### Common Issues

#### TTS Not Working
```bash
# Test espeak installation
espeak "Hello World"

# Check audio system
aplay /dev/zero
```

#### FFmpeg Issues
```bash
# Test FFmpeg
ffmpeg -version

# Install if missing
sudo apt-get install ffmpeg
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R app:app /app
chmod 755 uploads/ output/ logs/
```

#### Memory Issues
```bash
# Monitor memory usage
free -h
docker stats

# Increase worker count for high traffic
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

## 📊 Performance Optimization

### For High Traffic
1. **Use Redis for job queue** (implement Celery)
2. **Add database persistence** for job tracking
3. **Implement CDN** for static files
4. **Use multiple workers** with load balancer
5. **Enable caching** for repeated conversions

### Sample High-Performance Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    replicas: 3
    
  redis:
    image: redis:alpine
    
  nginx:
    image: nginx:alpine
    
  db:
    image: postgres:13
```

## 🔒 Security Best Practices

1. **Use HTTPS** in production
2. **Validate file types** strictly
3. **Implement rate limiting**
4. **Regular security updates**
5. **Monitor file uploads**
6. **Use firewall rules**
7. **Regular backups**

## 📈 Scaling Considerations

For production at scale:

1. **Horizontal scaling**: Multiple app instances
2. **Database**: PostgreSQL for job persistence  
3. **Queue system**: Redis + Celery for background jobs
4. **Storage**: S3/MinIO for file storage
5. **Monitoring**: Prometheus + Grafana
6. **Logging**: ELK stack or similar

---

## 🎯 Quick Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Configure `.env` file
- [ ] Set up HTTPS/SSL
- [ ] Configure monitoring
- [ ] Set up automated backups
- [ ] Test file cleanup
- [ ] Configure log rotation
- [ ] Set up health checks
- [ ] Test disaster recovery
- [ ] Configure alerts

Your PDF to Audio converter is now ready for production deployment! 🚀