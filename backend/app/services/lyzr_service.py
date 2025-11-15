"""Lyzr Agent API service for code review analysis"""
import httpx
import uuid
from typing import Optional
from loguru import logger

from app.config import settings
from app.models.lyzr import LyzrRequest, LyzrResponse


class LyzrService:
    """Service for interacting with Lyzr Agent API"""
    
    def __init__(self):
        self.api_key = settings.LYZR_API_KEY
        self.agent_id = settings.LYZR_AGENT_ID
        self.api_url = settings.LYZR_API_URL
        self.user_id = settings.DEFAULT_USER_ID
    
    def _generate_session_id(self, pr_number: int, repo: str) -> str:
        """Generate a unique session ID for the PR review"""
        base = f"{self.agent_id}-{repo}-pr{pr_number}"
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{base}-{unique_suffix}"
    
    async def analyze_pr_diff(
        self,
        pr_diff: str,
        pr_number: int,
        repo: str,
        additional_context: Optional[str] = None
    ) -> LyzrResponse:
        """
        Send PR diff to Lyzr agent for analysis
        
        Args:
            pr_diff: Unified diff string
            pr_number: PR number
            repo: Repository name
            additional_context: Optional additional context (file contents, etc.)
            
        Returns:
            Lyzr agent response
        """
        session_id = self._generate_session_id(pr_number, repo)
        
        # Construct message for the agent
        message = self._format_review_message(pr_diff, additional_context)
        
        # Build request payload
        request_data = LyzrRequest(
            user_id=self.user_id,
            agent_id=self.agent_id,
            session_id=session_id,
            message=message
        )
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Sending PR diff to Lyzr agent (session: {session_id})")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data.model_dump()
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Received response from Lyzr agent: {len(str(data))} chars")
                
                return LyzrResponse(**data)
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Lyzr API: {e}")
            return LyzrResponse(error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error calling Lyzr API: {e}")
            return LyzrResponse(error=str(e))
    
    def _format_review_message(self, pr_diff: str, additional_context: Optional[str] = None) -> str:
        """Format the PR diff and context into a message for the agent"""
        message_parts = [
            "Please review the following pull request diff and provide structured feedback.",
            "",
            "## PR DIFF",
            "```diff",
            pr_diff[:50000],
            "```"
        ]
        
        if additional_context:
            message_parts.extend([
                "",
                "## ADDITIONAL CONTEXT",
                additional_context[:10000]
            ])
        
        message_parts.extend([
            "",
            "## CRITICAL: EXACT OUTPUT FORMAT REQUIRED",
            "",
            "You MUST use this EXACT format (do not deviate):",
            "",
            "### Inline Comments:",
            "",
            "- **Location:** path/to/file.ts:10-15",
            "  - **Severity:** Critical|Major|Minor|Suggestion",
            "  - **Category:** Logic|Performance|Security|Typesafety|Accessibility|Readability|Testing|Maintainability",
            "  - **Summary:** One sentence summary.",
            "  - **Explanation:** 2-4 sentence explanation of the issue and impact.",
            "  - **Suggested fix (confidence: 95%):**",
            "    ```ts",
            "    // code snippet here",
            "    ```",
            "  - **Confidence:** 95%",
            "",
            "### Grouped Summary:",
            "",
            "- **CategoryName:** X Major, Y Minor",
            "  - #1 Severity: description, files: file.ts, remediation: steps, confidence: 90%",
            "",
            "### Prioritized Action List:",
            "1. Action description (Severity) — reason",
            "2. Another action (Severity) — reason",
            "3. Third action (Severity) — reason",
            "",
            "Focus on TypeScript, React, logic, performance, security, accessibility, and type safety issues.",
            "Use the EXACT format above - our parser depends on it."
        ])
        
        return "\n".join(message_parts)
    
    async def chat_with_agent(
        self,
        agent_id: str,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Generic method to chat with any Lyzr agent
        
        Args:
            agent_id: Lyzr agent ID
            message: Message to send
            user_id: User ID
            session_id: Optional session ID (auto-generated if not provided)
            
        Returns:
            Agent's response text
        """
        if not session_id:
            session_id = f"{agent_id}-{uuid.uuid4()}"
        
        request_data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "message": message
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Calling agent {agent_id}")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract response text
                if isinstance(data, dict):
                    return data.get("response", str(data))
                return str(data)
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling agent {agent_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling agent {agent_id}: {e}")
            raise
    
    def parse_agent_response(self, response: LyzrResponse) -> dict:
        """Parse the agent's response into structured data"""
        if response.error:
            raise ValueError(f"Agent returned error: {response.error}")
        
        if not response.response:
            raise ValueError("Agent returned empty response")
        
        return {
            "raw_response": response.response,
            "agent_id": response.agent_id,
            "session_id": response.session_id,
            "metadata": response.metadata
        }


LyzrAgentClient = LyzrService
