"""
Tests for GitHub service
"""
import pytest
from app.services.github_service import GitHubService


class TestGitHubService:
    """Test cases for GitHubService"""
    
    def test_parse_pr_url_valid(self):
        """Test parsing valid PR URLs"""
        service = GitHubService()
        
        test_cases = [
            ("https://github.com/owner/repo/pull/123", ("owner", "repo", 123)),
            ("http://github.com/test-org/test-repo/pull/456", ("test-org", "test-repo", 456)),
            ("https://github.com/user-123/repo_name/pull/1", ("user-123", "repo_name", 1)),
        ]
        
        for url, expected in test_cases:
            result = service.parse_pr_url(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_parse_pr_url_invalid(self):
        """Test parsing invalid PR URLs"""
        service = GitHubService()
        
        invalid_urls = [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/issues/123",
            "not-a-url",
            "https://gitlab.com/owner/repo/pull/123",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                service.parse_pr_url(url)
    
    def test_verify_webhook_signature_no_secret(self):
        """Test webhook signature verification with no secret configured"""
        service = GitHubService()
        
        # Should pass if no secret is configured (warning mode)
        result = service.verify_webhook_signature(b"test", "")
        assert result is True


@pytest.mark.asyncio
class TestGitHubServiceAsync:
    """Async test cases for GitHubService"""
    
    async def test_get_pr_details_invalid_token(self):
        """Test get_pr_details with invalid credentials"""
        service = GitHubService()
        service.token = "invalid_token"
        service.headers["Authorization"] = "Bearer invalid_token"
        
        with pytest.raises(Exception):
            await service.get_pr_details("owner", "repo", 123)
