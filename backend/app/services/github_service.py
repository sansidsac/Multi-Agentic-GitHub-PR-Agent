"""GitHub API service for fetching PR data and posting reviews"""
import httpx
import re
from typing import Optional, Tuple, List, Dict, Any
from loguru import logger

from app.config import settings


class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Tuple of (owner, repo, pr_number)
            
        Raises:
            ValueError: If URL format is invalid
        """
        pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, pr_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
        
        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)
    
    async def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch PR details from GitHub API
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PR details as dictionary
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Fetch PR diff from GitHub API
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            Unified diff string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {
            **self.headers,
            "Accept": "application/vnd.github.v3.diff"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
    
    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch list of changed files in PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            List of file change objects
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        """
        Fetch file content from repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch/commit SHA)
            
        Returns:
            File content as string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            # Decode base64 content
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
    
    async def post_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: Optional[int] = None,
        start_line: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Post a review comment on a specific line in a PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Comment text
            commit_id: Commit SHA
            path: File path
            line: End line number (for single line or range)
            start_line: Start line number (for multi-line comments)
            
        Returns:
            Comment object
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        
        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
        }
        
        if start_line and start_line != line:
            payload["start_line"] = start_line
            payload["start_side"] = "RIGHT"
        
        payload["side"] = "RIGHT"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a PR review with optional inline comments
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            commit_id: Commit SHA
            body: Review summary
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
            comments: List of inline comments
            
        Returns:
            Review object
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "commit_id": commit_id,
            "body": body,
            "event": event
        }
        
        if comments:
            payload["comments"] = comments
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def post_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Post a general comment on PR (not inline)
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Comment text
            
        Returns:
            Comment object
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        payload = {"body": body}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    def verify_webhook_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """
        Verify GitHub webhook signature
        
        Args:
            payload_body: Raw webhook payload
            signature_header: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not settings.GITHUB_WEBHOOK_SECRET:
            logger.warning("No webhook secret configured, skipping verification")
            return True
        
        import hmac
        import hashlib
        
        if not signature_header:
            return False
        
        # GitHub sends signature as "sha256=<signature>"
        hash_algorithm, github_signature = signature_header.split("=")
        
        # Calculate expected signature
        secret = settings.GITHUB_WEBHOOK_SECRET.encode()
        expected_signature = hmac.new(secret, payload_body, hashlib.sha256).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(expected_signature, github_signature)
