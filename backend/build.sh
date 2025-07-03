#!/bin/bash
# Simplified build script for Render deployment

echo "Starting build process..."
echo "Python version: $(python --version)"

# Just upgrade pip and install requirements - let Render handle the rest
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"