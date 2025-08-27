# Railway Deployment Guide for Axie Studio Backend

## 🚀 Quick Start

Your Axie Studio backend is now **Railway-ready**! Follow these steps to deploy:

### 1. Connect GitHub Repository to Railway

1. Go to [Railway.app](https://railway.app)
2. Sign in with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose `axiestudio/backend` repository
6. Railway will automatically detect the configuration

### 2. Environment Variables Setup

In your Railway project dashboard, add these environment variables:

#### Required Variables
```bash
# Core Settings
AXIESTUDIO_HOST=0.0.0.0
AXIESTUDIO_BACKEND_ONLY=true
AXIESTUDIO_LOG_LEVEL=info

# Authentication (CHANGE THESE!)
AXIESTUDIO_SUPERUSER=admin
AXIESTUDIO_SUPERUSER_PASSWORD=your-secure-password-here
AXIESTUDIO_SECRET_KEY=your-very-secure-secret-key-here

# Auto-login (set to false for production)
AXIESTUDIO_AUTO_LOGIN=false
```

#### Optional Database (Recommended for Production)
```bash
# Add PostgreSQL service in Railway, then use:
AXIESTUDIO_DATABASE_URL=$DATABASE_URL
AXIESTUDIO_DATABASE_CONNECTION_RETRY=true
```

#### Optional Redis (For Caching)
```bash
# Add Redis service in Railway, then use:
AXIESTUDIO_REDIS_URL=$REDIS_URL
```

### 3. Deploy

1. Railway will automatically start building and deploying
2. The build process will:
   - Install Python dependencies
   - Set up the Axie Studio environment
   - Start the backend server
3. Your app will be available at the Railway-provided URL

## 📁 Files Created for Railway

- **`railway.json`** - Railway configuration
- **`Procfile`** - Process definition
- **`nixpacks.toml`** - Build configuration
- **`start.py`** - Production startup script
- **`requirements.txt`** - Python dependencies
- **`.env.railway`** - Environment variables reference

## 🔧 Configuration Details

### Port Configuration
Railway automatically provides the `$PORT` environment variable. The app is configured to:
- Listen on `0.0.0.0:$PORT`
- Use Railway's dynamic port assignment

### Health Check
- Health check endpoint: `/health`
- Timeout: 300 seconds
- Restart policy: On failure (max 3 retries)

### Backend-Only Mode
The deployment runs in backend-only mode (`AXIESTUDIO_BACKEND_ONLY=true`) which:
- Disables frontend serving
- Optimizes for API-only usage
- Reduces resource usage

## 🛠 Troubleshooting

### Build Issues
1. Check Railway build logs
2. Ensure all dependencies are in `base/pyproject.toml`
3. Verify Python version compatibility

### Runtime Issues
1. Check Railway deployment logs
2. Verify environment variables are set correctly
3. Ensure database connection (if using PostgreSQL)

### Common Environment Variables
```bash
# Debug mode (only for development)
AXIESTUDIO_DEV=false

# Logging
AXIESTUDIO_LOG_LEVEL=info

# Database pool settings (for high traffic)
AXIESTUDIO_POOL_SIZE=10
AXIESTUDIO_MAX_OVERFLOW=20
```

## 🔐 Security Recommendations

1. **Change default credentials**:
   - Set strong `AXIESTUDIO_SUPERUSER_PASSWORD`
   - Generate secure `AXIESTUDIO_SECRET_KEY`

2. **Use PostgreSQL for production**:
   - Add PostgreSQL service in Railway
   - Set `AXIESTUDIO_DATABASE_URL`

3. **Enable Redis for caching**:
   - Add Redis service in Railway
   - Set `AXIESTUDIO_REDIS_URL`

## 📊 Monitoring

Railway provides built-in monitoring for:
- CPU usage
- Memory usage
- Network traffic
- Application logs

## 🔄 Updates

To update your deployment:
1. Push changes to the `main` branch
2. Railway will automatically redeploy
3. Monitor the deployment in Railway dashboard

## 🆘 Support

If you encounter issues:
1. Check Railway deployment logs
2. Review environment variables
3. Ensure GitHub repository is properly connected
4. Verify all configuration files are present

Your backend is now ready for production deployment on Railway! 🎉
