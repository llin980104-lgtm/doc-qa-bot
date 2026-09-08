"""
Test suite for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestQAEndpoint:
    def test_qa_valid_query(self):
        """Test Q&A with valid query"""
        response = client.post(
            "/api/v1/qa",
            json={"query": "What is Doc QA Bot?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "layer" in data
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1

    def test_qa_empty_query(self):
        """Test Q&A with empty query"""
        response = client.post(
            "/api/v1/qa",
            json={"query": ""}
        )
        assert response.status_code in [400, 404]

    def test_qa_include_confidence(self):
        """Test Q&A with confidence flag"""
        response = client.post(
            "/api/v1/qa",
            json={
                "query": "How to start?",
                "include_confidence": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data

    def test_qa_include_sources(self):
        """Test Q&A with sources flag"""
        response = client.post(
            "/api/v1/qa",
            json={
                "query": "How to start?",
                "include_sources": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data


class TestDocumentEndpoint:
    def test_add_document(self):
        """Test adding document"""
        response = client.post(
            "/api/v1/documents",
            json={
                "doc_id": "test-doc",
                "content": "Test document content",
                "source": "test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestFeedbackEndpoint:
    def test_submit_feedback(self):
        """Test submitting feedback"""
        response = client.post(
            "/api/v1/feedback",
            json={
                "query": "Test question",
                "answer": "Test answer",
                "rating": 5,
                "comment": "Good"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestStatsEndpoint:
    def test_get_stats(self):
        """Test getting system statistics"""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "general" in data
        assert "total_queries" in data["general"]
