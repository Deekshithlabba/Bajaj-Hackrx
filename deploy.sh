#!/bin/bash

# Deployment script for HackRx Document Intelligence System
# Handles different Python versions and package compatibility

echo "Starting deployment..."

# Upgrade pip and build tools
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Install packages based on Python version
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "Using Python 3.13 compatible packages..."
    pip install -r requirements_minimal.txt
elif [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo "Using Python 3.12 compatible packages..."
    pip install -r requirements_render.txt
else
    echo "Using default packages..."
    pip install -r requirements.txt
fi

echo "Deployment completed successfully!" 