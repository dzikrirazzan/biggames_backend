#!/bin/bash
# Render build script for BigGames Backend

set -e  # Exit on error

echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download Hugging Face model
echo "🤖 Downloading Hugging Face model..."
echo "⚠️  This may take a few minutes on first deployment..."

python3 << 'EOF'
import os
from sentence_transformers import SentenceTransformer

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

try:
    print(f"📥 Downloading model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"✅ Model downloaded successfully!")
    print(f"📊 Model dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    print(f"❌ Failed to download model: {e}")
    print("⚠️  Model will be downloaded on first API request")
    exit(0)  # Don't fail build, model can be loaded at runtime
EOF

echo "✅ Build completed successfully!"
