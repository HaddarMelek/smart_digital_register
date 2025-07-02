#!/bin/bash
# Build script for Render deployment

set -e  # Exit on any error

echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Upgrade pip to latest version
pip install --upgrade pip

# Install build tools with specific versions for compatibility
pip install --no-cache-dir setuptools==69.0.3 wheel==0.42.0

# Set environment variables for better compatibility
export SETUPTOOLS_USE_DISTUTILS=stdlib
export PIP_USE_PEP517=1

# Install requirements with verbose output for debugging
pip install --no-cache-dir --verbose -r requirements.txt

echo "Build completed successfully!"