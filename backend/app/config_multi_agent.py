"""Multi-Agent Configuration - Defines all agents in the review system"""

from typing import List
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    agent_id: str
    name: str
    description: str
    focus_areas: List[str]
    category: str


# Define all specialist agents (4 total)
SPECIALIST_AGENTS = {
    "performance": AgentConfig(
        agent_id="6918709b3ce080cebc84efbc",
        name="Performance Specialist",
        description="Detects performance bottlenecks",
        focus_areas=["Re-renders", "Memoization", "Algorithms", "Memory Leaks"],
        category="Performance"
    ),
    "typesafety": AgentConfig(
        agent_id="6918711534fa533a0e5725b6",
        name="TypeScript Safety Specialist",
        description="Ensures type correctness",
        focus_areas=["Type Assertions", "Any Usage", "Null Safety", "Generics"],
        category="Typesafety"
    ),
    "react": AgentConfig(
        agent_id="691871575848af7d875ae40c",
        name="React & UX Specialist",
        description="Reviews React patterns and accessibility",
        focus_areas=["Hooks", "Accessibility", "Component Design", "UX"],
        category="ReactBestPractices"
    ),
    "logic": AgentConfig(
        agent_id="6918718434fa533a0e5725ce",
        name="Logic & Code Quality Specialist",
        description="Analyzes business logic and code quality",
        focus_areas=["Logic Bugs", "Error Handling", "Edge Cases", "Maintainability"],
        category="Logic"
    )
}

MANAGER_AGENT = AgentConfig(
    agent_id="69186fc73ce080cebc84efb1",
    name="PR Review Manager",
    description="Coordinates specialist agents and produces final review",
    focus_areas=["Orchestration", "Aggregation", "Deduplication"],
    category="Management"
)


class MultiAgentStrategy:
    """Defines how to execute multi-agent reviews"""
    
    @staticmethod
    def should_invoke_agent(agent_key: str, diff: str, file_paths: List[str]) -> bool:
        """
        Determine if an agent should be invoked based on diff content
        Optimization: skip agents that have nothing to review
        """
        # Performance agent: invoke for components and hooks
        if agent_key == "performance":
            perf_keywords = ["useEffect", "useState", "useMemo", "useCallback", "map(", "render"]
            return any(kw in diff for kw in perf_keywords)
        
        # TypeSafety agent: always invoke for .ts/.tsx files
        if agent_key == "typesafety":
            return any(fp.endswith(('.ts', '.tsx')) for fp in file_paths)
        
        # React agent: invoke for component files
        if agent_key == "react":
            react_keywords = ["React", "Component", "Hook", "jsx", "tsx"]
            return any(kw in diff for kw in react_keywords)
        
        # Logic agent: always invoke (general code quality)
        if agent_key == "logic":
            return True
        
        return True  # Default: invoke all agents
