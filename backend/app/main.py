"""FastAPI main application - Multi-Agent PR Review System"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.routers import webhook_router
from app.routers import multi_agent_review

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)

app = FastAPI(
    title="GitHub PR Review Agent",
    description="Automated code review agent powered by Lyzr Agent Studio (Multi-Agent System)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/api/v1")
app.include_router(multi_agent_review.router, prefix="/api/v1/review")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "GitHub PR Review Agent (Multi-Agent)",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "webhook": "/api/v1/webhook/github",
            "multi_agent_review": "/api/v1/review/multi/pr",
            "health": "/health"
        },
        "agents": {
            "specialists": 4,
            "manager": 1,
            "total": 5
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "github_token_configured": bool(settings.GITHUB_TOKEN),
        "lyzr_api_configured": bool(settings.LYZR_API_KEY and settings.LYZR_AGENT_ID),
        "webhook_secret_configured": bool(settings.GITHUB_WEBHOOK_SECRET)
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("="*80)
    logger.info("GitHub PR Review Agent Starting...")
    logger.info("="*80)
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"GitHub token configured: {'✓' if settings.GITHUB_TOKEN else '✗'}")
    logger.info(f"Lyzr agent configured: {'✓' if settings.LYZR_AGENT_ID else '✗'}")
    logger.info(f"Webhook secret configured: {'✓' if settings.GITHUB_WEBHOOK_SECRET else '✗'}")
    logger.info("="*80)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("GitHub PR Review Agent Shutting Down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
