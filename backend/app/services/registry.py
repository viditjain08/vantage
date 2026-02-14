from typing import List, Dict

# Seeded registry data
SEEDED_REGISTRY: Dict[str, List[Dict[str, str]]] = {
    "coding": [
        {"name": "GitHub Writer", "url": "https://mcp.github.com/writer", "description": "integration with GitHub issues and PRs"},
        {"name": "Postgres Manager", "url": "https://mcp.postgres.com/server", "description": "Manage Postgres databases"},
    ],
    "data": [
        {"name": "Pandas Analysis", "url": "https://mcp.pandas.com/server", "description": "Data analysis using Pandas"},
        {"name": "SQL Explorer", "url": "https://mcp.sql-explorer.com", "description": "Explore SQL databases"},
    ],
    "general": [
        {"name": "Web Search", "url": "https://mcp.brave.com/search", "description": "Search the web"},
        {"name": "Calculator", "url": "https://mcp.calculator.com", "description": "Basic calculator"},
    ]
}

class RegistryService:
    @staticmethod
    def suggest_servers(category_name: str) -> List[Dict[str, str]]:
        """
        Suggest MCP servers based on category name matching.
        Simple keyword matching for Phase 1.
        """
        category_lower = category_name.lower()
        suggestions = []
        
        # Check exact matches or substring matches
        for key, servers in SEEDED_REGISTRY.items():
            if key in category_lower:
                suggestions.extend(servers)
        
        # Default to general if no specific match
        if not suggestions:
            suggestions.extend(SEEDED_REGISTRY["general"])
            
        return suggestions
