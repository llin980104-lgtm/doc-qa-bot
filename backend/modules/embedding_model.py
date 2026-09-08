"""
Embedding Model - Layer 2 (Small Model)

Vector-based semantic search using lightweight embedding models.
Typical latency: <500ms, Accuracy: 85-90%
"""
import numpy as np
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from config import settings
import pickle
from pathlib import Path


class EmbeddingModel:
    """Embedding model for semantic search"""

    def __init__(self, model_name: str = None, device: str = None):
        """Initialize embedding model"""
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.device = device or settings.EMBEDDING_DEVICE
        
        # Load pre-trained model
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # In-memory cache for embeddings
        self.embedding_cache = {}

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embedding vectors
        
        Args:
            texts: List of text strings
            
        Returns:
            Array of shape (len(texts), embedding_dim)
        """
        # Check cache first
        uncached_texts = []
        uncached_indices = []
        cached_embeddings = {}
        
        for i, text in enumerate(texts):
            text_hash = hash(text)
            if text_hash in self.embedding_cache:
                cached_embeddings[i] = self.embedding_cache[text_hash]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Encode uncached texts
        if uncached_texts:
            new_embeddings = self.model.encode(
                uncached_texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Cache results
            for i, text in zip(uncached_indices, uncached_texts):
                text_hash = hash(text)
                embedding = new_embeddings[uncached_indices.index(i)]
                self.embedding_cache[text_hash] = embedding
                cached_embeddings[i] = embedding
        
        # Reconstruct in original order
        embeddings = np.zeros((len(texts), self.embedding_dim))
        for i in range(len(texts)):
            embeddings[i] = cached_embeddings[i]
        
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text to embedding"""
        return self.encode([text])[0]

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Returns:
            Similarity score in range [0, 1]
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        # Normalize to [0, 1]
        return (similarity + 1) / 2

    def most_similar(self, query_embedding: np.ndarray, 
                     corpus_embeddings: np.ndarray,
                     top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding vector
            corpus_embeddings: Corpus embeddings (N x D matrix)
            top_k: Number of top results
            
        Returns:
            List of (index, similarity_score) tuples
        """
        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        corpus_norm = corpus_embeddings / np.linalg.norm(
            corpus_embeddings, axis=1, keepdims=True
        )
        
        # Calculate similarities
        similarities = np.dot(corpus_norm, query_norm)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            score = (similarities[idx] + 1) / 2  # Normalize to [0, 1]
            results.append((idx, float(score)))
        
        return results

    def save_embeddings(self, embeddings: np.ndarray, save_path: str):
        """Save embeddings to file"""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        np.save(save_path, embeddings)

    def load_embeddings(self, save_path: str) -> Optional[np.ndarray]:
        """Load embeddings from file"""
        if Path(save_path).exists():
            return np.load(save_path)
        return None

    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'cached_embeddings': len(self.embedding_cache),
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
        }
