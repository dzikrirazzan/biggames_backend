"""Embedding provider for AI recommendations using Hugging Face."""
import numpy as np


class HuggingFaceEmbeddingProvider:
    """Hugging Face embedding provider using sentence-transformers.
    
    Uses paraphrase-multilingual-MiniLM-L12-v2 model:
    - Free and offline after initial download (~100MB)
    - Supports multilingual text including Bahasa Indonesia
    - 384-dimensional embeddings
    - Fast on CPU
    - Great for Indonesian language support
    """
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self._model = None
        self._dimension = 384
        self.model_name = model_name
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading Hugging Face model: {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                print(f"Model loaded successfully with dimension: {self._dimension}")
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers torch"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load Hugging Face model '{self.model_name}': {e}"
                )
    
    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding using Hugging Face model."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        self._load_model()
        
        try:
            # sentence-transformers encode is synchronous but fast
            # Using show_progress_bar=False for cleaner API usage
            embedding = self._model.encode(
                text, 
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True  # Built-in normalization
            )
            
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to get embedding from Hugging Face: {e}")


def get_embedding_provider() -> HuggingFaceEmbeddingProvider:
    """Get Hugging Face embedding provider.
    
    Uses sentence-transformers with paraphrase-multilingual-MiniLM-L12-v2 model.
    Free, offline, and supports Indonesian language.
    """
    return HuggingFaceEmbeddingProvider()
