#!/bin/bash
# Deployment script for HackRx 6.0 Document Intelligence System
# Optimized for Render deployment

set -e  # Exit on any error

echo "🚀 Starting HackRx 6.0 deployment..."

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies with verbose output
echo "📦 Installing dependencies..."
if ! pip install -r requirements.txt --verbose; then
    echo "⚠️ Main requirements failed, trying minimal requirements..."
    pip install -r requirements_minimal.txt --verbose
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp_documents
mkdir -p processed_chunks
mkdir -p document_cache

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 temp_documents
chmod 755 processed_chunks
chmod 755 document_cache

echo "✅ Deployment setup complete!" 