# Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Pandas Compilation Errors

**Problem**: Pandas fails to compile from source on Python 3.13
```
error: too few arguments to function '_PyLong_AsByteArray'
```

**Solution**: 
- Use Python 3.12 instead of 3.13
- Use specific pandas version (2.2.3) that has pre-compiled wheels
- Use `requirements_render.txt` instead of `requirements.txt`

### 2. Package Version Not Found

**Problem**: pip cannot find specified package version
```
ERROR: No matching distribution found for pandas==2.2.4
```

**Solution**:
- Check available versions: `pip index versions pandas`
- Use the latest available version in the series
- For pandas, use 2.2.3 (latest in 2.2.x series)

### 3. Build Timeout Issues

**Problem**: Build takes too long and times out

**Solutions**:
- Use pre-compiled wheels when possible
- Pin specific versions instead of using ranges
- Upgrade pip, setuptools, and wheel before installing requirements

### 4. Memory Issues During Build

**Problem**: Build fails due to insufficient memory

**Solutions**:
- Use lighter dependencies
- Consider upgrading to a higher Render plan
- Use pre-compiled wheels to reduce compilation memory usage

## Deployment Checklist

### Before Deploying:
1. ✅ Use Python 3.12 runtime
2. ✅ Use `requirements_render.txt` 
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
pip install --upgrade pip setuptools wheel
pip install -r requirements_render.txt
```

### Start Command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Alternative Solutions

### If pandas still fails:
1. Try using `pandas==2.1.5` (last 2.1.x version)
2. Consider removing pandas if not essential
3. Use alternative data processing libraries

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