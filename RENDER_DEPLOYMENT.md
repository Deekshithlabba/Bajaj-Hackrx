# 🚀 Render Deployment Guide
**HackRx 6.0 Document Intelligence System**

## 📋 Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: 
   - Google Gemini API Key (free tier available)
   - Pinecone API Key

## 🛠️ Deployment Steps

### 1. **Prepare Your Repository**

Ensure these files are in your repository root:
- ✅ `requirements.txt` (production dependencies)
- ✅ `render.yaml` (deployment configuration)
- ✅ `main.py` (FastAPI application)
- ✅ All Python modules (.py files)

### 2. **Deploy to Render**

#### Option A: Using render.yaml (Recommended)
1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

#### Option B: Manual Setup
1. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure settings:

```
Name: hackrx-document-intelligence
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. **Configure Environment Variables**

In Render Dashboard → Your Service → Environment:

```bash
# Required API Keys
GEMINI_API_KEY=your_actual_gemini_key_here
PINECONE_API_KEY=your_actual_pinecone_key_here

# Optional Configuration
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=50
VISION_MODEL=gpt-4o
MAX_VISION_TOKENS=500
```

### 4. **Deploy**

- **Automatic**: Render deploys automatically on git push to main branch
- **Manual**: Click "Manual Deploy" in dashboard

## 🔍 Verify Deployment

### Health Check
```bash
curl https://your-app-name.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.123456",
  "details": {
    "document_pipeline": true,
    "vector_pipeline": true,
    "llm_pipeline": true
  }
}
```

### Test API
```bash
curl -X POST "https://your-app-name.onrender.com/hackrx/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GEMINI_API_KEY" \
  -d '{
    "documents": "https://example.com/sample.pdf",
    "questions": ["What is this document about?"]
  }'
```

## 🎯 Production Optimizations

### 1. **Upgrade Render Plan**
- **Starter**: Free (with limitations)
- **Standard**: $7/month (recommended for production)
- **Pro**: $25/month (high performance)

### 2. **Add Redis Caching** (Optional)
Uncomment Redis section in `render.yaml`:
```yaml
- type: redis
  name: hackrx-cache
  plan: starter
  region: oregon
```

### 3. **Add Custom Domain**
In Render Dashboard → Your Service → Settings → Custom Domains

### 4. **Enable Auto-Deploy**
Render automatically deploys on git push to the connected branch.

## 🐛 Troubleshooting

### Common Issues

1. **Build Fails**:
   - Check Python version compatibility
   - Verify all dependencies in `requirements.txt`
   - Check build logs in Render dashboard

2. **API Key Errors**:
   - Verify environment variables are set correctly
   - Ensure OpenAI API key has billing enabled
   - Check Pinecone API key permissions

3. **Memory Issues**:
   - Consider upgrading to Standard/Pro plan
   - Optimize batch sizes in `config.py`

4. **Timeout Issues**:
   - Increase request timeout in Render settings
   - Monitor response times with 3-second delays between API calls

### Log Monitoring
- **Render Logs**: Dashboard → Your Service → Logs
- **Application Logs**: Built-in FastAPI logging
- **Performance**: Dashboard → Your Service → Metrics

## 📊 Expected Performance

- **Cold Start**: ~30-60 seconds (first request after idle)
- **Warm Requests**: ~2-5 minutes (with 3-second API delays)
- **Concurrent Requests**: Supported (FastAPI async)

## 🎉 Success!

Your HackRx 6.0 Document Intelligence System is now deployed and ready for production use!

**Live API Endpoint**: `https://your-app-name.onrender.com`

---

**Need Help?** 
- Check Render documentation: [render.com/docs](https://render.com/docs)
- Review application logs in Render dashboard
- Test locally first: `python main.py`