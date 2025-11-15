"""
Lyzr Agent API models
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class LyzrRequest(BaseModel):
    """Request model for Lyzr Agent API"""
    user_id: str
    agent_id: str
    session_id: str
    message: str


class LyzrResponse(BaseModel):
    """Response model from Lyzr Agent API"""
    response: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
