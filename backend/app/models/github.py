"""
GitHub-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class User(BaseModel):
    """GitHub user model"""
    login: str
    id: int
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None


class Repository(BaseModel):
    """GitHub repository model"""
    id: int
    name: str
    full_name: str
    owner: User
    html_url: str
    description: Optional[str] = None
    private: bool = False
    default_branch: str = "main"


class PullRequest(BaseModel):
    """GitHub pull request model"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    user: User
    html_url: str
    diff_url: str
    head: Dict[str, Any]
    base: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    merged: bool = False


class WebhookPayload(BaseModel):
    """GitHub webhook payload model"""
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    sender: User


class ReviewRequest(BaseModel):
    """Manual PR review request"""
    pr_url: str = Field(..., description="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    auto_post: bool = Field(default=True, description="Automatically post review comments to GitHub")


class ReviewComment(BaseModel):
    """Individual review comment"""
    path: str = Field(..., description="File path")
    position: Optional[int] = Field(None, description="Position in diff (for inline comments)")
    line: Optional[int] = Field(None, description="Line number in file")
    body: str = Field(..., description="Comment text")
    severity: str = Field(..., description="Critical/Major/Minor/Suggestion")
    category: str = Field(..., description="Logic/Performance/Security/etc")
    confidence: int = Field(..., description="Confidence percentage")


class ReviewSummary(BaseModel):
    """Grouped review summary"""
    category: str
    severity: str
    count: int
    items: List[str]


class ReviewResponse(BaseModel):
    """PR review response"""
    pr_number: int
    pr_url: str
    repository: str
    inline_comments: List[ReviewComment]
    grouped_summary: List[ReviewSummary]
    prioritized_actions: List[str]
    posted_to_github: bool
    review_url: Optional[str] = None


class PRReviewRequest(BaseModel):
    """PR review request with owner/repo/number"""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number")
    auto_post: bool = Field(default=False, description="Automatically post review comments to GitHub")


class InlineComment(BaseModel):
    """Inline code comment"""
    path: str = Field(..., description="File path")
    line: int = Field(..., description="End line number")
    start_line: Optional[int] = Field(None, description="Start line number (for multi-line comments)")
    body: str = Field(..., description="Comment text")
    
    class Config:
        populate_by_name = True


class ReviewAction(BaseModel):
    """Prioritized action item"""
    priority: int = Field(..., description="Priority order (1=highest)")
    action: str = Field(..., description="Action description")


class PRReviewResponse(BaseModel):
    """PR review response with inline comments"""
    pr_number: int
    pr_url: str
    repository: str
    inline_comments: List[InlineComment]
    actions: List[str]
    summary: str
    posted_to_github: bool = False
    review_url: Optional[str] = None
