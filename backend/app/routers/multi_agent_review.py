"""
Multi-Agent Review Router
API endpoint for multi-agent PR reviews
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from loguru import logger
import re

from app.models.github import PRReviewResponse
from app.services.github_service import GitHubService
from app.services.lyzr_service import LyzrService
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator


router = APIRouter(prefix="/multi", tags=["multi-agent-review"])

github_service = GitHubService()
lyzr_service = LyzrService()
multi_agent_orchestrator = MultiAgentOrchestrator(lyzr_service)


class MultiAgentReviewRequest(BaseModel):
    """Request model for multi-agent PR review"""
    pr_url: str = Field(..., description="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    auto_post: bool = Field(default=True, description="Automatically post review comments to GitHub")


@router.post("/pr", response_model=PRReviewResponse)
async def review_pr_multi_agent(
    request: MultiAgentReviewRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger a multi-agent PR review using specialist agents
    
    Uses 4 specialist agents (Performance, TypeSafety, React, Logic)
    coordinated by a manager agent to produce comprehensive reviews.
    """
    try:
        pr_url_pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pr_url_pattern, request.pr_url)
        
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub PR URL format")
        
        owner, repo, pr_number = match.groups()
        pr_number = int(pr_number)
        
        logger.info(f"Multi-agent review requested for {owner}/{repo}#{pr_number}")
        
        diff = await github_service.get_pr_diff(owner=owner, repo=repo, pr_number=pr_number)
        
        if not diff:
            raise HTTPException(status_code=404, detail="PR diff not found")
        
        logger.info(f"Fetched PR diff: {len(diff)} characters")
        
        pr_context = {
            "owner": owner,
            "repo": repo,
            "number": pr_number,
            "title": f"PR #{pr_number}"
        }
        
        review_data = await multi_agent_orchestrator.review_pr_diff(
            diff=diff,
            pr_context=pr_context,
            user_id=owner
        )
        
        review = PRReviewResponse(
            pr_number=pr_number,
            pr_url=request.pr_url,
            repository=f"{owner}/{repo}",
            inline_comments=review_data["inline_comments"],
            actions=review_data["actions"],
            summary=review_data["summary"],
            posted_to_github=False
        )
        
        if request.auto_post and review.inline_comments:
            try:
                logger.info("Posting review to GitHub...")
                
                pr_details = await github_service.get_pr_details(owner, repo, pr_number)
                commit_id = pr_details["head"]["sha"]
                
                github_comments = []
                for c in review.inline_comments:
                    comment = {
                        "path": c.path,
                        "line": c.line,
                        "body": c.body,
                        "side": "RIGHT"
                    }
                    if c.start_line and c.start_line != c.line:
                        comment["start_line"] = c.start_line
                        comment["start_side"] = "RIGHT"
                    github_comments.append(comment)
                
                result = await github_service.create_review(
                    owner=owner,
                    repo=repo,
                    pr_number=pr_number,
                    commit_id=commit_id,
                    body=review.summary or "🤖 Multi-agent automated code review completed.",
                    event="COMMENT",
                    comments=github_comments
                )
                
                review.posted_to_github = True
                review.review_url = result.get("html_url", "")
                logger.info(f"✅ Review posted successfully: {review.review_url}")
                
            except Exception as e:
                logger.error(f"❌ Failed to post review: {e}")
                review.posted_to_github = False
        
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-agent review failed: {e}")
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")
