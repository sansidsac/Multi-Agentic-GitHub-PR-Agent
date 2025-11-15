# GitHub PR Review Agent 🤖

**Multi-Agentic AI-Powered GitHub Pull Request Review System**

> **Problem Statement:** Manual code reviews are time-consuming and often miss critical issues across different domains (performance, security, type safety). This system automates comprehensive PR reviews using specialized AI agents.

---

## Solution Approach

I built an automated GitHub PR review system using **Lyzr's Agent Studio** with a **multi-agent architecture** for comprehensive code analysis.

**Architecture:**
Instead of using a single agent, I implemented **5 specialized AI agents** working together:
- **4 Specialist Agents** (GPT-4o-mini): Performance Specialist, TypeScript Safety Specialist, React/UX Specialist, and Logic & Code Quality Specialist - all run in parallel
- **1 Manager Agent** (GPT-4o): Aggregates findings, removes duplicates, and produces the final review

**Integration Methods:**
The system supports two ways to trigger reviews:
1. **GitHub Webhooks** - Automatically triggers reviews when PRs are opened/updated
2. **Manual API** - Direct PR URL submission via REST endpoint

For local development and testing, I used **DevTunnels** to expose localhost to GitHub's webhook system, allowing real-time testing without cloud deployment.

**Review Output:**
The system generates structured feedback in two formats:
- **Inline Comments** - Specific code suggestions pinned to exact line numbers with severity levels (Critical/Major/Minor) and confidence scores
- **Overall Summary** - Grouped findings by category with prioritized action items

**Tech Stack:**
- **Backend**: Python 3.12 + FastAPI (async REST API)
- **AI Platform**: Lyzr Agent Studio (GPT-4o, GPT-4o-mini)
- **Integration**: GitHub REST API + Webhooks
- **Key Libraries**: httpx (async HTTP), Pydantic (validation), asyncio (parallel execution)

The multi-agent orchestrator runs specialists in parallel using asyncio, then passes findings to the manager for intelligent aggregation and deduplication.

---

## Key Features

✅ **Multi-Agent Architecture** - Parallel specialist analysis + intelligent aggregation  
✅ **Dual Integration** - Webhook automation + Manual API endpoint  
✅ **Structured Output** - Inline comments + grouped summary + prioritized actions  
✅ **Production Ready** - Error handling, logging, validation, testing  

---

## Architecture

**Multi-Agent Flow:**
```
GitHub PR → Orchestrator → [4 Specialists in Parallel] → Manager Agent → Final Review → GitHub
```

**Project Structure:**
```
backend/
├── app/
│   ├── main.py                          # FastAPI application
│   ├── config_multi_agent.py            # 5 Agent definitions
│   ├── routers/
│   │   ├── webhook.py                   # Webhook endpoint
│   │   └── multi_agent_review.py        # Manual review API
│   └── services/
│       ├── github_service.py            # GitHub API client
│       ├── lyzr_service.py              # Lyzr Agent client
│       └── multi_agent_orchestrator.py  # Parallel execution logic
└── requirements.txt
```

---

## Quick Setup

### Installation
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuration
Create `backend/.env`:
```env
GITHUB_TOKEN=your_token
GITHUB_WEBHOOK_SECRET=your_secret
LYZR_API_KEY=your_key
LYZR_AGENT_ID=your_agent_id
DEFAULT_USER_ID=your_email
```

### Run
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoints:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

---

## Usage

### Method 1: Manual API Call
```bash
curl -X POST http://localhost:8000/api/v1/review/multi/pr \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://github.com/owner/repo/pull/123", "auto_post": true}'
```

### Method 2: GitHub Webhook (DevTunnels)
```bash
# Start devtunnel
devtunnel host -p 8000 --allow-anonymous

# Configure webhook in GitHub:
# URL: https://your-tunnel.devtunnels.ms/api/v1/webhook/github
# Events: Pull requests
```

---

## Sample Output

**Inline Comment:**
```
Path: src/components/Button.tsx (Lines 42-45)
Severity: Major | Category: Performance
Issue: Unnecessary re-renders due to missing memoization
Suggested Fix: Wrap component with React.memo()
Confidence: 95%
```

**Overall Summary:**
```
- Performance: 2 Major, 1 Minor
- TypeSafety: 1 Critical
- Logic: 3 Minor
Priority Actions: Fix memory leak, Add type guards, Optimize loops
```

---

## Technical Highlights

- **Async Execution**: Specialists run in parallel using `asyncio.gather()`
- **Error Handling**: Graceful degradation if agents fail
- **Smart Routing**: Agents only invoked if relevant to diff content
- **Deduplication**: Manager removes overlapping findings
- **GitHub API**: Proper handling of inline comments with line ranges
- **Validation**: Pydantic models ensure data integrity
- **Logging**: Structured logging with Loguru for debugging

---

## Status

✅ Production Ready | ✅ Tested on Live PRs | ✅ Clean Codebase

**Author:** K S Sreekumar | kssreekumar04@gmail.com  
**Last Updated:** November 15, 2025
