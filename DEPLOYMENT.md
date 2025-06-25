# Smart School Management - Deployment Guide

## 🚀 Vercel Deployment Configuration

### Frontend Configuration
- **Framework**: React.js
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Root Directory**: `frontend`

### Environment Variables Required
```
REACT_APP_API_URL=https://your-backend-url.com/api
REACT_APP_APP_NAME=Alexander Academy
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production
```

### Features
- ✅ Single Page Application (SPA) routing
- ✅ Static asset caching
- ✅ Environment-based API configuration
- ✅ Production optimized build

### Live URLs
- **Frontend**: https://smart-school-managment.vercel.app
- **Repository**: https://github.com/ohaddar/smart_school_managment

## 📋 Deployment Steps
1. Push code to GitHub
2. Connect Vercel to GitHub repository
3. Configure build settings
4. Add environment variables
5. Deploy!