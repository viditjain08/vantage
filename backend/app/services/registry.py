import json
import logging
import re
from typing import Any, List, Dict, TYPE_CHECKING
from langchain_core.messages import HumanMessage
from app.services.llm_factory import LLMFactory

if TYPE_CHECKING:
    from app.models.category import Category

logger = logging.getLogger(__name__)

# Curated list of well-known MCP servers
MCP_SERVER_CATALOG: List[Dict[str, Any]] = [
    # Developer tools
    {"name": "GitHub", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/github", "description": "GitHub API integration for issues, PRs, repos, and code search"},
    {"name": "GitLab", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/gitlab", "description": "GitLab API integration for projects, merge requests, and CI/CD"},
    {"name": "Git", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/git", "description": "Git operations including diff, log, commit, and branch management"},

    # Databases
    {"name": "PostgreSQL", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres", "description": "Query and manage PostgreSQL databases"},
    {"name": "MySQL", "url": "https://github.com/benborla/mcp-server-mysql", "description": "Query and manage MySQL databases"},
    {"name": "MongoDB", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/mongodb", "description": "Query and manage MongoDB databases"},
    {"name": "Redis", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/redis", "description": "Redis cache and data store operations"},
    {"name": "SQLite", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite", "description": "Query and manage SQLite databases"},

    # Cloud platforms
    {
        "name": "AWS", "url": "", "type": "stdio",
        "description": "AWS services including S3, Lambda, EC2, CloudWatch, and more (via AWS MCP proxy)",
        "config_schema": [
            {"name": "AWS_ACCESS_KEY_ID", "label": "Access Key ID", "type": "text", "required": True, "placeholder": "AKIA..."},
            {"name": "AWS_SECRET_ACCESS_KEY", "label": "Secret Access Key", "type": "password", "required": True, "placeholder": ""},
            {"name": "AWS_DEFAULT_REGION", "label": "Region", "type": "text", "required": True, "placeholder": "us-east-1"},
        ],
        "stdio_config": {
            "command": "uvx",
            "args": ["mcp-proxy-for-aws@latest", "https://aws-mcp.us-east-1.api.aws/mcp"],
        },
    },
    {
        "name": "Azure", "url": "https://github.com/mashriram/azure_mcp_server", "description": "Azure cloud services and resource management",
        "config_schema": [
            {"name": "azure_tenant_id", "label": "Tenant ID", "type": "text", "required": True, "placeholder": ""},
            {"name": "azure_client_id", "label": "Client ID", "type": "text", "required": True, "placeholder": ""},
            {"name": "azure_client_secret", "label": "Client Secret", "type": "password", "required": True, "placeholder": ""},
            {"name": "azure_subscription_id", "label": "Subscription ID", "type": "text", "required": True, "placeholder": ""},
        ],
    },
    {
        "name": "GCP", "url": "https://github.com/rishikavikondala/gcp-mcp", "description": "Google Cloud Platform services and management",
        "config_schema": [
            {"name": "gcp_project_id", "label": "Project ID", "type": "text", "required": True, "placeholder": "my-project-id"},
            {"name": "gcp_service_account_json", "label": "Service Account JSON", "type": "textarea", "required": True, "placeholder": "{\"type\": \"service_account\", ...}"},
        ],
    },
    {
        "name": "Kubernetes", "url": "https://github.com/strowk/mcp-k8s-go", "description": "Kubernetes cluster management and operations",
        "config_schema": [
            {"name": "k8s_cluster_endpoint", "label": "Cluster Endpoint", "type": "text", "required": True, "placeholder": "https://k8s.example.com:6443"},
            {"name": "k8s_token", "label": "Bearer Token", "type": "password", "required": True, "placeholder": ""},
            {"name": "k8s_namespace", "label": "Namespace", "type": "text", "required": False, "placeholder": "default"},
        ],
    },
    {"name": "Docker", "url": "https://github.com/docker/docker-mcp", "description": "Docker container and image management"},
    {"name": "Terraform", "url": "https://github.com/hashicorp/terraform-mcp-server", "description": "Terraform infrastructure-as-code management"},

    # Collaboration & productivity
    {"name": "Confluence", "url": "https://github.com/sooperset/mcp-atlassian", "description": "Atlassian Confluence wiki pages, spaces, and content management"},
    {"name": "Jira", "url": "https://github.com/sooperset/mcp-atlassian", "description": "Atlassian Jira issue tracking, project management, and workflows"},
    {"name": "Slack", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack", "description": "Slack messaging, channels, and workspace management"},
    {"name": "Google Drive", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive", "description": "Google Drive file management and search"},
    {"name": "Google Workspace", "url": "https://github.com/pab1it0/google-workspace-mcp", "description": "Gmail, Calendar, Docs, and Sheets integration"},
    {"name": "Notion", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/notion", "description": "Notion pages, databases, and workspace management"},
    {"name": "Linear", "url": "https://github.com/jerhadf/linear-mcp-server", "description": "Linear issue tracking and project management"},

    # Observability & logging
    {"name": "Elasticsearch", "url": "https://github.com/elastic/mcp-server-elasticsearch", "description": "Elasticsearch search, indexing, and cluster management"},
    {"name": "Kibana", "url": "https://github.com/nicholasgriffintn/kibana-mcp-server", "description": "Kibana dashboards and log visualization"},
    {"name": "Grafana", "url": "https://github.com/grafana/mcp-grafana", "description": "Grafana dashboards, alerts, and data source management"},
    {"name": "Datadog", "url": "https://github.com/winor30/mcp-server-datadog", "description": "Datadog monitoring, metrics, and alerting"},
    {"name": "Sentry", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sentry", "description": "Sentry error tracking and performance monitoring"},

    # Web & search
    {"name": "Brave Search", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search", "description": "Web search via Brave Search API"},
    {"name": "Fetch", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch", "description": "Fetch and parse web page content"},
    {"name": "Puppeteer", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer", "description": "Browser automation, scraping, and screenshots"},

    # Finance & business
    {"name": "Bloomberg", "url": "https://github.com/pab1it0/bloomberg-mcp", "description": "Bloomberg financial data and market information"},
    {"name": "Stripe", "url": "https://github.com/stripe/agent-toolkit", "description": "Stripe payments, subscriptions, and billing management"},
    {"name": "Plaid", "url": "https://github.com/plaid/plaid-mcp-server", "description": "Plaid banking and financial data aggregation"},

    # File systems & storage
    {"name": "Filesystem", "url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "description": "Local filesystem read, write, and search operations"},
    {
        "name": "S3", "url": "", "type": "stdio",
        "description": "Amazon S3 bucket and object management",
        "stdio_config": {
            "command": "uvx",
            "args": ["mcp-proxy-for-aws@latest", "https://aws-mcp.us-east-1.api.aws/mcp"],
        },
    },
    {"name": "Google Cloud Storage", "url": "https://github.com/pab1it0/gcs-mcp", "description": "Google Cloud Storage bucket and object management"},

    # Communication
    {"name": "Email (SMTP)", "url": "https://github.com/ai-mcp/mcp-server-email", "description": "Send and manage emails via SMTP"},
    {"name": "Microsoft Teams", "url": "https://github.com/pab1it0/ms-teams-mcp", "description": "Microsoft Teams messaging and channel management"},

    # Data & analytics
    {"name": "Snowflake", "url": "https://github.com/isaacwasserman/mcp-snowflake-server", "description": "Snowflake data warehouse querying and management"},
    {"name": "BigQuery", "url": "https://github.com/ergut/mcp-bigquery-server", "description": "Google BigQuery data querying and management"},
    {"name": "Pandas", "url": "https://github.com/pab1it0/pandas-mcp", "description": "Data analysis and manipulation with Pandas"},

    # CI/CD & DevOps
    {"name": "Jenkins", "url": "https://github.com/Multi-Agent-LLM/mcp-jenkins-server", "description": "Jenkins CI/CD pipeline management and job execution"},
    {"name": "CircleCI", "url": "https://github.com/circleci/mcp-server-circleci", "description": "CircleCI pipeline and workflow management"},
    {"name": "Vercel", "url": "https://github.com/nicholasgriffintn/vercel-mcp-server", "description": "Vercel deployments, projects, and domain management"},

    # Security
    {"name": "Vault", "url": "https://github.com/pab1it0/vault-mcp", "description": "HashiCorp Vault secrets management"},
    {"name": "Snyk", "url": "https://github.com/snyk/snyk-mcp", "description": "Snyk vulnerability scanning and security management"},
]


class RegistryService:
    @staticmethod
    def _get_llm_from_category(category: "Category"):
        """Build an LLM instance from the category's stored LLM configuration."""
        return LLMFactory.create_llm(
            provider=category.llm_provider,
            model=category.llm_model,
            provider_type=category.llm_provider_type,
            api_key=category.llm_api_key,
            endpoint=category.llm_endpoint,
            api_version=category.llm_api_version,
            deployment_name=category.llm_deployment_name,
            region=category.llm_region,
        )

    @classmethod
    async def suggest_servers(cls, category: "Category") -> List[Dict[str, Any]]:
        """
        Suggest MCP servers for a category.
        Uses the category's LLM to pick the top 3 from the curated catalog.
        Falls back to keyword matching if LLM is unavailable.
        """
        category_name = category.name

        # 1. Try LLM-based selection
        try:
            llm = cls._get_llm_from_category(category)
            server_list_str = "\n".join(
                f"- {s['name']}: {s['description']}" for s in MCP_SERVER_CATALOG
            )
            prompt = (
                f"Given the user's agent category '{category_name}', pick the most relevant MCP servers "
                f"from the following list. Return ONLY a JSON array of the server names, nothing else.\n\n"
                f"Servers:\n{server_list_str}"
            )
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            match = re.search(r"\[.*\]", response.content, re.DOTALL)
            if match:
                selected_names = json.loads(match.group())
                suggestions = []
                for name in selected_names:
                    for s in MCP_SERVER_CATALOG:
                        if s["name"] == name:
                            suggestions.append(s)
                            break
                if suggestions:
                    logger.info(f"LLM suggestions for '{category_name}': {[s['name'] for s in suggestions]}")
                    return suggestions[:3]
        except Exception as e:
            logger.error(f"LLM suggestion failed: {e}")

        # 2. Fallback: simple keyword matching
        category_lower = category_name.lower()
        suggestions = [
            s for s in MCP_SERVER_CATALOG
            if category_lower in s["name"].lower() or category_lower in s["description"].lower()
        ]
        return suggestions[:3] if suggestions else MCP_SERVER_CATALOG[:3]
