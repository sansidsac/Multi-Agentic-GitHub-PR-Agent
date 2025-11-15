"""GitHub webhook endpoint for automated PR reviews"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from typing import Optional
from loguru import logger

from app.services.github_service import GitHubService
from app.services.lyzr_service import LyzrService
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
from app.models.github import WebhookPayload

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None)
):
    """GitHub webhook endpoint for PR events (opened, reopened, synchronized)"""
    body = await request.body()
    
    github_service = GitHubService()
    if not github_service.verify_webhook_signature(body, x_hub_signature_256 or ""):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload_dict = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(f"Received GitHub webhook: {x_github_event}")
    
    if x_github_event != "pull_request":
        return {"status": "ignored", "message": f"Event type '{x_github_event}' is not handled"}
    
    try:
        payload = WebhookPayload(**payload_dict)
    except Exception as e:
        logger.error(f"Invalid webhook payload structure: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")
    
    if payload.action not in ["opened", "reopened", "synchronize"]:
        return {"status": "ignored", "message": f"Action '{payload.action}' is not handled"}
    
    owner = payload.repository.owner.login
    repo = payload.repository.name
    pr_number = payload.pull_request.number
    
    logger.info(f"Processing PR webhook: {owner}/{repo}#{pr_number} (action: {payload.action})")
    background_tasks.add_task(
        process_pr_review,
        owner=owner,
        repo=repo,
        pr_number=pr_number
    )
    
    return {
        "status": "accepted",
        "message": f"PR review queued for {owner}/{repo}#{pr_number}",
        "pr_url": payload.pull_request.html_url
    }


async def process_pr_review(owner: str, repo: str, pr_number: int):
    """Background task to process PR review using multi-agent system"""
    try:
        logger.info(f"Starting multi-agent PR review: {owner}/{repo}#{pr_number}")
        
        github_service = GitHubService()
        lyzr_service = LyzrService()
        orchestrator = MultiAgentOrchestrator(lyzr_service)
        
        diff = await github_service.get_pr_diff(owner, repo, pr_number)
        
        if not diff:
            logger.error(f"Could not fetch diff for {owner}/{repo}#{pr_number}")
            return
        
        pr_context = {"owner": owner, "repo": repo, "number": pr_number, "title": f"PR #{pr_number}"}
        
        review_data = await orchestrator.review_pr_diff(
            diff=diff,
            pr_context=pr_context,
            user_id=owner
        )
        
        if review_data["inline_comments"]:
            pr_details = await github_service.get_pr_details(owner, repo, pr_number)
            commit_id = pr_details["head"]["sha"]
            
            github_comments = []
            for c in review_data["inline_comments"]:
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
                body=review_data["summary"] or "🤖 Multi-agent automated code review completed.",
                event="COMMENT",
                comments=github_comments
            )
            
            review_url = result.get("html_url", "")
            logger.info(f"✅ Multi-agent review completed: {owner}/{repo}#{pr_number}")
            logger.info(f"Posted {len(github_comments)} comments, review URL: {review_url}")
        else:
            logger.info(f"No comments to post for {owner}/{repo}#{pr_number}")
        
    except Exception as e:
        logger.error(f"Failed to process multi-agent PR review for {owner}/{repo}#{pr_number}: {e}")


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook"""
    return {
        "status": "healthy",
        "endpoint": "github_webhook",
        "events": ["pull_request"]
    }
