"""
Integration tests for the API
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPI:
    """Test cases for API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GitHub PR Review Agent"
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_webhook_health(self):
        """Test webhook health endpoint"""
        response = client.get("/api/v1/webhook/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_review_health(self):
        """Test review health endpoint"""
        response = client.get("/api/v1/review/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_review_pr_invalid_url(self):
        """Test review endpoint with invalid PR URL"""
        response = client.post(
            "/api/v1/review/pr",
            json={"pr_url": "not-a-valid-url", "auto_post": False}
        )
        assert response.status_code == 400
    
    def test_webhook_invalid_event(self):
        """Test webhook with non-PR event"""
        response = client.post(
            "/api/v1/webhook/github",
            json={"action": "created", "issue": {}},
            headers={"X-GitHub-Event": "issues"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
