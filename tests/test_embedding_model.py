"""
Test suite for embedding model
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from modules.embedding_model import EmbeddingModel


@pytest.fixture
def embedding_model():
    """Create embedding model instance"""
    return EmbeddingModel(model_name="distilbert-base-uncased", device="cpu")


def test_encode_single(embedding_model):
    """Test encoding single text"""
    text = "This is a test sentence."
    embedding = embedding_model.encode_single(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] == embedding_model.embedding_dim


def test_encode_batch(embedding_model):
    """Test encoding batch of texts"""
    texts = [
        "First document",
        "Second document",
        "Third document"
    ]
    embeddings = embedding_model.encode(texts)
    
    assert embeddings.shape == (3, embedding_model.embedding_dim)


def test_similarity(embedding_model):
    """Test similarity calculation"""
    text1 = "The cat sat on the mat"
    text2 = "The dog lay on the rug"
    text3 = "The cat sat on the mat"
    
    emb1 = embedding_model.encode_single(text1)
    emb2 = embedding_model.encode_single(text2)
    emb3 = embedding_model.encode_single(text3)
    
    sim1_2 = embedding_model.similarity(emb1, emb2)
    sim1_3 = embedding_model.similarity(emb1, emb3)
    
    # Similar sentences should have higher similarity
    assert sim1_3 > sim1_2
    assert 0 <= sim1_2 <= 1
    assert 0 <= sim1_3 <= 1


def test_most_similar(embedding_model):
    """Test finding most similar embeddings"""
    query = "How to use the system?"
    corpus = [
        "Getting started with the system",
        "Installation guide",
        "API reference documentation"
    ]
    
    query_emb = embedding_model.encode_single(query)
    corpus_embs = embedding_model.encode(corpus)
    
    results = embedding_model.most_similar(query_emb, corpus_embs, top_k=2)
    
    assert len(results) <= 2
    assert all(isinstance(score, float) for _, score in results)


def test_cache(embedding_model):
    """Test embedding caching"""
    text = "Test document"
    
    # First encoding
    emb1 = embedding_model.encode_single(text)
    
    # Second encoding (from cache)
    emb2 = embedding_model.encode_single(text)
    
    # Should be identical (from cache)
    np.testing.assert_array_equal(emb1, emb2)
    
    # Cache should have 1 entry
    stats = embedding_model.get_cache_stats()
    assert stats['cached_embeddings'] == 1


def test_clear_cache(embedding_model):
    """Test clearing cache"""
    embedding_model.encode_single("Test")
    embedding_model.clear_cache()
    
    stats = embedding_model.get_cache_stats()
    assert stats['cached_embeddings'] == 0
