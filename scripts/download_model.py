#!/usr/bin/env python3
"""Download Hugging Face model for embeddings."""
import sys

print("Downloading Hugging Face model...")
print("Model: paraphrase-multilingual-MiniLM-L12-v2")
print("This may take a few minutes on first run...")

try:
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    print(f"✓ Model downloaded successfully!")
    print(f"  Dimension: {model.get_sentence_embedding_dimension()}")
    
    # Test encoding
    test_text = "Test embedding untuk room VIP"
    embedding = model.encode(test_text)
    print(f"✓ Test encoding successful! Vector size: {len(embedding)}")
    
except Exception as e:
    print(f"✗ Error downloading model: {e}")
    sys.exit(1)

print("\n✅ Ready to use!")
