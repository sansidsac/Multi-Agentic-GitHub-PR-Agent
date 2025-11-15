"""Multi-Agent Orchestrator Service - Coordinates multiple specialist agents"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from loguru import logger

from app.config_multi_agent import SPECIALIST_AGENTS, MANAGER_AGENT, MultiAgentStrategy
from app.services.lyzr_service import LyzrAgentClient
from app.models.github import PRReviewResponse, InlineComment, ReviewAction


class MultiAgentOrchestrator:
    """Orchestrates multiple specialist agents for comprehensive PR reviews"""
    
    def __init__(self, lyzr_client: LyzrAgentClient):
        self.lyzr_client = lyzr_client
        self.strategy = MultiAgentStrategy()
    
    async def review_pr_diff(
        self,
        diff: str,
        pr_context: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-agent PR review
        
        Args:
            diff: The PR diff to review
            pr_context: Context about the PR (owner, repo, number, etc.)
            user_id: User ID for Lyzr API
            
        Returns:
            Dictionary with review results (not PRReviewResponse - that's created by router)
        """
        try:
            logger.info("Starting multi-agent PR review")
            
            specialist_findings = await self._invoke_specialists(diff, pr_context, user_id)
            manager_response = await self._invoke_manager(specialist_findings, diff, user_id)
            review = self._parse_manager_response(manager_response)
            
            logger.info(f"Multi-agent review complete: {len(review['inline_comments'])} comments")
            return review
            
        except Exception as e:
            logger.error(f"Multi-agent orchestration failed: {e}")
            raise
    
    async def _invoke_specialists(
        self,
        diff: str,
        pr_context: Dict[str, Any],
        user_id: str
    ) -> Dict[str, List[Dict]]:
        """Invoke all specialist agents in parallel"""
        
        file_paths = self._extract_file_paths(diff)
        findings = {}
        
        tasks = []
        agent_keys = []
        
        for agent_key, agent_config in SPECIALIST_AGENTS.items():
            if self.strategy.should_invoke_agent(agent_key, diff, file_paths):
                logger.info(f"Invoking {agent_config.name}")
                task = self._invoke_specialist_agent(
                    agent_config.agent_id,
                    agent_config.name,
                    diff,
                    pr_context,
                    user_id
                )
                tasks.append(task)
                agent_keys.append(agent_key)
            else:
                logger.info(f"Skipping {agent_config.name} (not relevant)")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for agent_key, result in zip(agent_keys, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_key} failed: {result}")
                findings[agent_key] = []
            else:
                findings[agent_key] = result
        
        return findings
    
    async def _invoke_specialist_agent(
        self,
        agent_id: str,
        agent_name: str,
        diff: str,
        pr_context: Dict[str, Any],
        user_id: str
    ) -> List[Dict]:
        """Invoke a single specialist agent"""
        
        try:
            message = f"""Review this pull request diff and identify issues in your area of expertise.

PR Context:
- Repository: {pr_context.get('owner')}/{pr_context.get('repo')}
- PR Number: {pr_context.get('number')}
- Title: {pr_context.get('title', 'N/A')}

Diff:
```
{diff[:5000]}
```

Return your findings as a JSON array following the specified format."""

            response = await self.lyzr_client.chat_with_agent(
                agent_id=agent_id,
                message=message,
                user_id=user_id
            )
            
            findings = self._parse_specialist_response(response, agent_name)
            logger.info(f"{agent_name} found {len(findings)} issues")
            
            return findings
            
        except Exception as e:
            logger.error(f"Failed to invoke {agent_name}: {e}")
            return []
    
    def _parse_specialist_response(self, response: str, agent_name: str) -> List[Dict]:
        """Parse specialist agent JSON response"""
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                findings = json.loads(json_str)
                return findings if isinstance(findings, list) else []
            
            findings = json.loads(response)
            return findings if isinstance(findings, list) else []
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {agent_name} response as JSON: {e}")
            return []
    
    async def _invoke_manager(
        self,
        specialist_findings: Dict[str, List[Dict]],
        diff: str,
        user_id: str
    ) -> str:
        """Send findings to manager agent for aggregation"""
        
        logger.info("Invoking Manager agent to aggregate findings")
        
        findings_summary = json.dumps(specialist_findings, indent=2)
        
        message = f"""You are receiving findings from the specialist review agents. Please aggregate these findings, remove duplicates, and produce a final review.

Specialist Findings:
{findings_summary}

Original Diff Context (first 1000 chars):
```
{diff[:1000]}
```

Please follow your instructions to produce the final review in the exact markdown format specified."""

        try:
            response = await self.lyzr_client.chat_with_agent(
                agent_id=MANAGER_AGENT.agent_id,
                message=message,
                user_id=user_id
            )
            
            logger.info(f"Manager response received ({len(response)} chars)")
            return response
            
        except Exception as e:
            logger.error(f"Manager agent failed: {e}")
            raise
    
    def _parse_manager_response(self, response: str) -> Dict[str, Any]:
        """Parse manager's markdown response"""
        
        try:
            logger.info(f"Parsing manager response ({len(response)} chars)")
            
            start_marker = "---START REVIEW---"
            end_marker = "---END REVIEW---"
            
            start_idx = response.find(start_marker)
            end_idx = response.find(end_marker)
            
            if start_idx == -1 or end_idx == -1:
                logger.error("Manager response missing delimiters")
                logger.error(f"Response preview: {response[:500]}...")
                raise ValueError("Invalid manager response format")
            
            review_content = response[start_idx + len(start_marker):end_idx].strip()
            logger.info(f"Extracted review content ({len(review_content)} chars)")
            
            inline_comments = self._parse_inline_comments_from_markdown(review_content)
            logger.info(f"Parsed {len(inline_comments)} inline comments")
            
            action_objects = self._parse_actions_from_markdown(review_content)
            actions = [action.action for action in action_objects]
            logger.info(f"Parsed {len(actions)} actions")
            
            summary = self._extract_summary_from_markdown(review_content)
            logger.info(f"Extracted summary ({len(summary)} chars)")
            
            return {
                "inline_comments": inline_comments,
                "actions": actions,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Failed to parse manager response: {e}")
            logger.error(f"Response: {response[:1000]}...")
            raise
    
    def _parse_inline_comments_from_markdown(self, content: str) -> List[InlineComment]:
        """Extract inline comments from markdown"""
        
        comments = []
        
        pattern = r'####\s+\d+\.\s+(.+?)\s+\(Lines\s+(\d+)-(\d+)\)(.*?)(?=####|\n### |$)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            file_path = match.group(1).strip()
            line_start = int(match.group(2))
            line_end = int(match.group(3))
            comment_body = match.group(4).strip()
            
            severity = self._extract_field(comment_body, "Severity")
            category = self._extract_field(comment_body, "Category")
            summary = self._extract_field(comment_body, "Summary")
            explanation = self._extract_field(comment_body, "Explanation")
            suggested_fix = self._extract_field(comment_body, "Suggested Fix")
            
            comment = InlineComment(
                path=file_path,
                line=line_end,
                start_line=line_start if line_start != line_end else None,
                body=f"**{severity} - {category}**\n\n{summary}\n\n{explanation}\n\n**Suggested Fix:**\n{suggested_fix}"
            )
            comments.append(comment)
        
        logger.info(f"Parsed {len(comments)} inline comments from manager response")
        return comments
    
    def _parse_actions_from_markdown(self, content: str) -> List[ReviewAction]:
        """Extract prioritized actions from markdown"""
        
        actions = []
        
        # Find Prioritized Actions section
        actions_section = re.search(r'### Prioritized Actions(.*?)(?=\n###|$)', content, re.DOTALL)
        if not actions_section:
            return actions
        
        actions_text = actions_section.group(1)
        
        # Pattern: 1. **Action description** (Severity - Category)
        pattern = r'\d+\.\s+\*\*(.+?)\*\*\s+\((.+?)\)'
        
        matches = re.finditer(pattern, actions_text)
        
        priority = 1
        for match in matches:
            description = match.group(1).strip()
            severity_category = match.group(2).strip()
            
            action = ReviewAction(
                action=description,
                priority=priority
            )
            actions.append(action)
            priority += 1
        
        logger.info(f"Parsed {len(actions)} prioritized actions")
        return actions[:5]  # Limit to top 5
    
    def _extract_summary_from_markdown(self, content: str) -> str:
        """Extract review summary section"""
        
        summary_section = re.search(r'### Review Summary(.*?)(?=---END REVIEW---|$)', content, re.DOTALL)
        if summary_section:
            return summary_section.group(1).strip()
        
        return "Multi-agent review completed successfully."
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from markdown text"""
        
        pattern = rf'-\s+\*\*{field_name}:\*\*\s+(.+?)(?=\n-|\n\n|$)'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return "N/A"
    
    def _extract_file_paths(self, diff: str) -> List[str]:
        """Extract file paths from diff"""
        
        paths = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                # Extract path: diff --git a/src/file.ts b/src/file.ts
                parts = line.split()
                if len(parts) >= 4:
                    path = parts[2][2:]  # Remove 'a/' prefix
                    paths.append(path)
        
        return paths
