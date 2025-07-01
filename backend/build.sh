#!/bin/bash
# Build script for Render deployment

set -e  # Exit on any error

# Clean pip cache and upgrade tools
pip cache purge
pip install --upgrade pip

# Force install compatible setuptools and wheel
pip install --force-reinstall setuptools==68.2.2 wheel

# Install requirements with no cache to avoid conflicts
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"