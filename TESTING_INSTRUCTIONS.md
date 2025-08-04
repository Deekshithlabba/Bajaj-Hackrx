# 🧪 Local Testing Instructions - HackRx 6.0 Document Intelligence API

## 📋 **Overview**

Your API now uses the **Bearer token as the OpenAI API key** with automatic fallback to the environment variable. This guide provides comprehensive testing instructions.

## 🔧 **Setup Prerequisites**

### **1. Environment Setup**
```bash
# 1. Verify Python version
python --version  # Should be Python 3.10+

# 2. Activate virtual environment (if using one)
# For Windows:
venv\Scripts\activate
# For Mac/Linux:
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements_ingestion.txt

# 4. Verify installations
python -c "import fastapi, openai, pinecone; print('✅ All packages installed')"
```

### **2. Environment Variables Setup**
```bash
# Create .env file from template
cp environment_template.txt .env

# Edit .env file and add your keys:
# OPENAI_API_KEY=sk-your-fallback-key-here
# PINECONE_API_KEY=your-pinecone-key-here
# PINECONE_INDEX_NAME=hackrx-document-search
```

### **3. API Keys Required**
- **Primary**: OpenAI API key (passed as Bearer token)
- **Fallback**: OpenAI API key (in .env file)
- **Vector DB**: Pinecone API key (in .env file)

## 🚀 **Starting the Server**

### **Method 1: Direct Python**
```bash
# Start the FastAPI server
python main.py

# Expected output:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# 🚀 Initializing HackRx 6.0 Document Intelligence API
# 📝 Initializing Document Ingestion Pipeline...
# 🔍 Initializing Vector Database Pipeline...
# 🧠 Initializing Two-Stage LLM Pipeline...
# ✅ All pipelines initialized successfully!
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **Method 2: Uvicorn**
```bash
# Alternative startup method
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Use --reload for development (auto-restart on file changes)
```

## 🔍 **Basic Health Checks**

### **1. Root Endpoint Test**
```bash
curl http://localhost:8000
# Expected: {"status":"healthy","message":"HackRx 6.0 Document Intelligence API is running"}
```

### **2. Detailed Health Check**
```bash
curl http://localhost:8000/health
# Expected: Detailed system status with pipeline health
```

### **3. API Documentation**
Open in browser: `http://localhost:8000/docs`
- Interactive Swagger UI for testing
- All endpoints documented
- Try-it-out functionality

## 🧪 **API Testing Scenarios**

### **Scenario 1: Test with Valid OpenAI API Key as Bearer Token**

```bash
# Replace YOUR_OPENAI_API_KEY with your actual OpenAI API key
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer sk-your-actual-openai-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"],
    "questions": ["What is this document about?"]
  }'
```

**Expected Response:**
```json
{
  "request_id": "uuid-here",
  "results": [
    {
      "question": "What is this document about?",
      "answer": "Based on the document content...",
      "confidence": 0.85,
      "citations": [
        {
          "source": "dummy.pdf",
          "page": 1,
          "chunk_id": "doc_1_chunk_001",
          "excerpt": "This is a dummy PDF file...",
          "relevance_score": 0.92
        }
      ],
      "methodology": "two_stage_hybrid_rag",
      "processing_time": 15.5
    }
  ],
  "performance": {
    "total_processing_time": 25.7,
    "total_tokens_used": 3400,
    "estimated_total_cost": 0.12
  }
}
```

### **Scenario 2: Test with Invalid Bearer Token (Fallback)**

```bash
# Use invalid token - should fallback to environment key
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer invalid-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"],
    "questions": ["What is this document about?"]
  }'
```

**Expected Behavior:**
- Server logs show: "⚠️ Failed to initialize with provided API key"
- Server logs show: "🔄 Falling back to environment API key"
- Request processes successfully with fallback key

### **Scenario 3: Test with Multiple Documents and Questions**

```bash
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer sk-your-actual-openai-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
      "https://www.orimi.com/pdf-test.pdf"
    ],
    "questions": [
      "What are the main topics in these documents?",
      "How many pages are there in total?",
      "What type of content is included?"
    ]
  }'
```

## 🛠️ **Advanced Testing**

### **1. Performance Testing**
```bash
# Test caching - run same request twice
echo "First request (processing):"
time curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"], "questions": ["What is this about?"]}'

echo -e "\n\nSecond request (cached):"
time curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"], "questions": ["What is this about?"]}'
```

### **2. Error Handling Tests**

**Invalid Document URL:**
```bash
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["https://invalid-url.com/nonexistent.pdf"],
    "questions": ["What is this about?"]
  }'
```

**Missing Authorization:**
```bash
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"],
    "questions": ["What is this about?"]
  }'
# Expected: 401 Unauthorized
```

### **3. Load Testing (Optional)**
```bash
# Install apache bench for load testing
# Ubuntu: sudo apt-get install apache2-utils
# Mac: brew install apache2-utils

# Test with 10 concurrent requests
ab -n 10 -c 2 -H "Authorization: Bearer sk-your-key" -H "Content-Type: application/json" -p test_payload.json http://localhost:8000/hackrx/run
```

Create `test_payload.json`:
```json
{
  "documents": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"],
  "questions": ["What is this document about?"]
}
```

## 📊 **Monitoring and Debugging**

### **1. Server Logs**
Monitor server logs for:
- ✅ Successful pipeline initialization
- 🔑 API key usage messages
- 📄 Document processing progress
- 🤔 Question processing status
- ⚠️ Warnings and errors

### **2. Key Log Messages to Look For**
```
✅ Pipelines initialized with provided API key
⚠️ Failed to initialize with provided API key: [error]
🔄 Falling back to environment API key
🔍 Processing request [uuid]: X docs, Y questions
🔑 Using OpenAI API key: sk-xxxx...
📄 Processing document: [url]
🤔 Processing question: [question]
✅ Question answered: 0.85 confidence, 3 citations
🎉 Request [uuid] completed: 25.7s, 2 questions answered
```

### **3. Performance Metrics**
Monitor in response:
- `processing_time`: Per question processing time
- `total_processing_time`: End-to-end time
- `total_tokens_used`: Token consumption
- `estimated_total_cost`: Cost estimation

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. "Module not found" errors:**
```bash
pip install -r requirements_ingestion.txt
# Or install missing packages individually
```

**2. "Pinecone API key not found":**
```bash
# Check .env file has PINECONE_API_KEY set
cat .env | grep PINECONE
```

**3. "OpenAI API key invalid":**
- Verify your API key format starts with `sk-`
- Check API key has sufficient credits
- Test key with direct OpenAI API call

**4. "Document processing failed":**
- Verify document URL is accessible
- Check document is in supported format (PDF, DOCX)
- Ensure document is not too large (>50MB)

**5. Server won't start:**
- Check port 8000 is not in use: `lsof -i :8000`
- Verify all environment variables are set
- Check Python version compatibility

### **Debug Mode:**
```bash
# Run with debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('main.py').read())
"
```

## ✅ **Success Criteria**

Your API is working correctly if:

1. **✅ Server starts without errors**
2. **✅ Health check returns "healthy" status**
3. **✅ Bearer token is used as OpenAI API key**
4. **✅ Fallback to environment key works**
5. **✅ Documents are processed and indexed**
6. **✅ Questions receive intelligent answers**
7. **✅ Citations are included in responses**
8. **✅ Performance metrics are reasonable**

## 🎯 **Ready for Production**

Once local testing passes:
- All endpoints respond correctly
- Authentication works with bearer tokens
- Document processing is stable
- LLM responses include citations
- Error handling is graceful
- Performance is acceptable

**Your API is ready for deployment!** 🚀

## 📞 **Need Help?**

If you encounter issues:
1. Check server logs for specific error messages
2. Verify all API keys are valid and have credits
3. Test with simple documents first
4. Ensure all dependencies are installed
5. Check network connectivity for document URLs