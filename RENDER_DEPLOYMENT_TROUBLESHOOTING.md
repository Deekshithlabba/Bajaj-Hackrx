# Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Python Version Mismatch

**Problem**: Render uses Python 3.13 instead of 3.12
```
/opt/render/project/src/.venv/lib/python3.13/
```

**Solution**: 
- Use the deployment script (`deploy.sh`) that automatically detects Python version
- The script will use appropriate requirements based on Python version
- For Python 3.13: uses `requirements_minimal.txt`
- For Python 3.12: uses `requirements_render.txt`

### 2. Pandas Compilation Errors

**Problem**: Pandas fails to compile from source
```
error: too few arguments to function '_PyLong_AsByteArray'
```

**Solution**: 
- Use pandas 2.1.5 (last stable version in 2.1.x series)
- Use pre-compiled wheels when possible
- Use minimal requirements for Python 3.13

### 3. Package Version Not Found

**Problem**: pip cannot find specified package version
```
ERROR: No matching distribution found for pandas==2.2.4
```

**Solution**:
- Check available versions: `pip index versions pandas`
- Use the latest available version in the series
- For pandas, use 2.1.5 (stable version)

### 4. Build Timeout Issues

**Problem**: Build takes too long and times out

**Solutions**:
- Use pre-compiled wheels when possible
- Pin specific versions instead of using ranges
- Upgrade pip, setuptools, and wheel before installing requirements

### 5. Memory Issues During Build

**Problem**: Build fails due to insufficient memory

**Solutions**:
- Use lighter dependencies (`requirements_minimal.txt`)
- Consider upgrading to a higher Render plan
- Use pre-compiled wheels to reduce compilation memory usage

## Deployment Files

### Requirements Files:
- `requirements_minimal.txt`: Minimal packages for Python 3.13
- `requirements_render.txt`: Full packages for Python 3.12
- `requirements.txt`: Default packages

### Deployment Script:
- `deploy.sh`: Automatically detects Python version and installs appropriate packages

## Deployment Checklist

### Before Deploying:
1. ✅ Use Python 3.12 runtime in render.yaml
2. ✅ Use deployment script (`deploy.sh`)
3. ✅ Pin all package versions
4. ✅ Test locally with same Python version
5. ✅ Ensure all environment variables are set in Render dashboard

### Environment Variables Required:
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_CLOUD` (set to "aws")
- `PINECONE_REGION` (set to "us-east-1")

### Build Command:
```bash
chmod +x deploy.sh && ./deploy.sh
```

### Start Command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Alternative Solutions

### If deployment still fails:
1. Try using `requirements_minimal.txt` directly
2. Consider removing pandas if not essential
3. Use alternative data processing libraries
4. Consider using Docker deployment

### If build continues to fail:
1. Check Render logs for specific error messages
2. Try deploying with a minimal requirements file first
3. Consider using Docker deployment instead

## Monitoring Deployment

1. Check build logs in Render dashboard
2. Monitor application logs after deployment
3. Test health check endpoint: `/health`
4. Verify all API endpoints are working

## Rollback Strategy

If deployment fails:
1. Revert to previous working commit
2. Use previous working requirements file
3. Consider using a different Python runtime version
4. Try the minimal requirements approach 