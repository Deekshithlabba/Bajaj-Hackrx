# 📝 Deployment Checklist
**HackRx 6.0 Document Intelligence System - Render Deployment**

## ✅ Pre-Deployment Checklist

### 📁 **Files Ready**
- [ ] `requirements.txt` - Production dependencies
- [ ] `render.yaml` - Deployment configuration  
- [ ] `main.py` - FastAPI application
- [ ] `RENDER_DEPLOYMENT.md` - Deployment guide
- [ ] All Python modules (`.py` files)
- [ ] `.gitignore` (exclude `__pycache__/`, `.env`, etc.)

### 🔑 **API Keys Ready**
- [ ] OpenAI API Key (with billing enabled and quota)
- [ ] Pinecone API Key (with project created)
- [ ] Test both keys locally before deployment

### 🧪 **Local Testing Complete**
- [ ] Health endpoint: `GET /health` returns 200
- [ ] API endpoint: `POST /hackrx/run` works with valid data
- [ ] Bearer token authentication working
- [ ] All dependencies install successfully
- [ ] No critical errors in logs

### 📦 **Repository Setup**
- [ ] Code pushed to GitHub repository
- [ ] Repository is public or accessible to Render
- [ ] Main branch contains latest code
- [ ] No sensitive data (API keys) in code

## 🚀 Deployment Steps

### 1. **Create Render Service**
- [ ] Sign up/login to [render.com](https://render.com)
- [ ] Connect GitHub repository
- [ ] Choose "Blueprint" deployment (uses `render.yaml`)
- [ ] OR choose "Web Service" for manual setup

### 2. **Configure Environment Variables**
- [ ] Set `OPENAI_API_KEY` in Render dashboard
- [ ] Set `PINECONE_API_KEY` in Render dashboard
- [ ] Optional: Set other environment variables

### 3. **Deploy & Monitor**
- [ ] Trigger deployment
- [ ] Monitor build logs for errors
- [ ] Wait for deployment to complete (~5-10 minutes)
- [ ] Check service status in dashboard

## ✅ Post-Deployment Verification

### 🔍 **Basic Health Check**
```bash
curl https://your-app-name.onrender.com/health
```
- [ ] Returns HTTP 200
- [ ] JSON response shows "healthy" status
- [ ] All pipeline statuses are `true`

### 🧪 **API Functionality Test**
```bash
curl -X POST "https://your-app-name.onrender.com/hackrx/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  -d '{
    "documents": ["https://example.com/sample.pdf"], 
    "questions": ["What is this document about?"]
  }'
```
- [ ] Returns HTTP 200 (or appropriate error if API quota exceeded)
- [ ] JSON response with `answers` array
- [ ] No server crashes in logs

### 📊 **Performance Check**
- [ ] Response time acceptable (~2-5 minutes with delays)
- [ ] Memory usage within limits
- [ ] No timeout errors
- [ ] Service restarts automatically if needed

### 🔐 **Security Check**
- [ ] Bearer token authentication required
- [ ] Invalid tokens rejected with 401
- [ ] No API keys exposed in logs
- [ ] CORS configured properly

## 🎯 Production Ready!

### 📝 **Documentation**
- [ ] API endpoint URL documented
- [ ] Authentication method documented  
- [ ] Request/response format documented
- [ ] Rate limiting behavior documented

### 🔄 **Monitoring Setup**
- [ ] Render dashboard bookmarked
- [ ] Log monitoring configured
- [ ] Performance metrics reviewed
- [ ] Auto-deploy enabled (optional)

---

## 🚨 If Something Goes Wrong

### Build Failures
1. Check build logs in Render dashboard
2. Verify `requirements.txt` dependencies
3. Test `pip install -r requirements.txt` locally
4. Check Python version compatibility

### Runtime Errors
1. Check service logs in Render dashboard
2. Verify environment variables are set
3. Test API keys manually
4. Check OpenAI/Pinecone service status

### API Errors
1. Verify OpenAI API quota/billing
2. Check Pinecone index exists
3. Test with minimal request first
4. Review application logs for details

---

**✅ Deployment Complete!** 

Your HackRx 6.0 Document Intelligence System is live at:
`https://your-app-name.onrender.com`