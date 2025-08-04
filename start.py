#!/usr/bin/env python3
"""
Production startup script for HackRx 6.0 Document Intelligence System
Optimized for Render deployment with production settings
"""

import os
import uvicorn
from main import app

def start_production_server():
    """Start the FastAPI server with production-optimized settings"""
    
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Production settings
    uvicorn.run(
        app,  # Use the app instance directly
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=False,  # Disable reload in production
        workers=1,  # Single worker for Render's resource limits
        timeout_keep_alive=120,  # Extended timeout for long-running requests
        timeout_graceful_shutdown=30,
        limit_concurrency=10,  # Limit concurrent requests
        limit_max_requests=1000,  # Restart worker after processing 1000 requests
    )

if __name__ == "__main__":
    start_production_server()