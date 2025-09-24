#!/bin/bash

# Setup script for PDF RAG Pipeline

echo "==================================="
echo "PDF RAG Pipeline Setup"
echo "==================================="

# Create necessary directories
echo "Creating project directories..."
mkdir -p data/pdfs
mkdir -p data/processed
mkdir -p data/faiss_index
mkdir -p cache

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys"
fi

# Make CLI executable
chmod +x cli.py
chmod +x example_usage.py

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Nomic API key (optional)"
echo "2. Add PDF files to ./data/pdfs/"
echo "3. Run: python cli.py parse ./data/pdfs/"
echo "4. Run: python cli.py search"
echo ""
echo "For help: python cli.py --help"