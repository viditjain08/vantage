import logging
import time
import uuid
from typing import List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.models.category import Category
from app.services.llm_factory import LLMFactory
from app.schemas.task_graph import (
    TaskGraph,
    Subtask,
    SubtaskStatus,
    SubtaskExecutor,
    DecompositionResponse,
)

logger = logging.getLogger("app.decomposer")

DECOMPOSITION_SYSTEM_PROMPT = """\
You are a task planning assistant. Given a user message and conversation history, you must decide:

1. Whether the message requires multi-step task decomposition, OR
2. Whether it can be answered directly as a simple chat response.

DECOMPOSE when the message:
- Asks for a multi-step process (e.g., "deploy X", "set up Y", "migrate Z")
- Involves coordinating multiple tools or actions
- Has inherent sequential or parallel dependencies between steps
- Would benefit from tracking progress across multiple operations

DO NOT DECOMPOSE when the message:
- Is a simple question (e.g., "what is X?", "how does Y work?")
- Asks for a single atomic action
- Is conversational or clarifying

If you decide to decompose, produce a list of subtasks forming a DAG (directed acyclic graph).

Each subtask must specify:
- name: short descriptive name (2-5 words)
- description: what this subtask does (1-2 sentences)
- executor: "system" if the AI agent can do it with the available tools, or "user" if it requires \
the human to perform an action (e.g., run a local command, approve something, provide credentials)
- depends_on: list of other subtask names this depends on (empty list if no dependencies)
- tools: list of tool names from the available tools that this subtask would need (only for system executor). \
Select only the tools relevant to this specific subtask.

Rules for the dependency graph:
- It MUST be a valid DAG (no cycles)
- Subtasks with no dependencies can run in parallel
- Be granular but not excessively so (3-8 subtasks is typical)
- Order subtasks logically

Available tools the system executor can use:
{tool_list}

If a step requires capabilities not covered by these tools, mark it as a "user" executor.
"""


class TaskDecomposer:
    @staticmethod
    async def maybe_decompose(
        user_message: str,
        chat_history: List[BaseMessage],
        category: Category,
        available_tools: List[dict],
    ) -> Optional[TaskGraph]:
        """
        Ask the LLM whether this message requires decomposition.
        Returns a TaskGraph if decomposition is needed, None for normal chat.
        """
        try:
            llm = LLMFactory.create_llm(
                provider=category.llm_provider,
                model=category.llm_model,
                provider_type=category.llm_provider_type,
                api_key=category.llm_api_key,
                endpoint=category.llm_endpoint,
                api_version=category.llm_api_version,
                deployment_name=category.llm_deployment_name,
                region=category.llm_region,
                temperature=None,
            )

            # Format tool list for the prompt
            if available_tools:
                tool_list = "\n".join(
                    f"- {t['name']}: {t['description']}" for t in available_tools
                )
            else:
                tool_list = "(No tools available - mark all subtasks as 'user' executor)"

            system_prompt = DECOMPOSITION_SYSTEM_PROMPT.format(tool_list=tool_list)

            # Build messages: system prompt + recent chat history for context
            messages = [SystemMessage(content=system_prompt)]
            # Include last few messages for context (not the full history to save tokens)
            recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
            messages.extend(recent_history)

            # Use json_schema method for broad model compatibility
            structured_llm = llm.with_structured_output(
                DecompositionResponse, method="json_mode"
            )
            # Append instruction to return JSON since json_mode requires it in the prompt
            messages.append(HumanMessage(content=(
                "Respond with a JSON object matching this schema: "
                '{"should_decompose": bool, "reasoning": str, "subtasks": [{"name": str, "description": str, '
                '"executor": "system"|"user", "depends_on": [str], "tools": [str]}]}'
            )))

            logger.info("[Decomposition LLM Request] %d messages", len(messages))
            t0 = time.time()
            raw_response = await structured_llm.ainvoke(messages)
            logger.info("[Decomposition LLM Response] %.2fs", time.time() - t0)

            # Handle different response shapes from with_structured_output
            if isinstance(raw_response, DecompositionResponse):
                response = raw_response
            elif isinstance(raw_response, dict):
                response = DecompositionResponse(**raw_response)
            else:
                logger.warning("Unexpected response type from structured output: %s", type(raw_response))
                return None

            logger.info("Decomposition decision: should_decompose=%s, reasoning=%s", response.should_decompose, response.reasoning[:200] if response.reasoning else "")

            if not response.should_decompose or not response.subtasks:
                return None

            # Build the task graph: assign UUIDs and resolve name-based deps to IDs
            task_id = str(uuid.uuid4())
            name_to_id: dict[str, str] = {}
            subtasks: List[Subtask] = []

            # First pass: assign IDs
            for spec in response.subtasks:
                subtask_id = str(uuid.uuid4())
                name_to_id[spec.name] = subtask_id

            # Second pass: build Subtask objects with resolved dependencies
            for spec in response.subtasks:
                resolved_deps = []
                for dep_name in spec.depends_on:
                    dep_id = name_to_id.get(dep_name)
                    if dep_id:
                        resolved_deps.append(dep_id)

                subtasks.append(Subtask(
                    id=name_to_id[spec.name],
                    name=spec.name,
                    description=spec.description,
                    executor=SubtaskExecutor(spec.executor),
                    dependencies=resolved_deps,
                    tools=spec.tools if spec.executor == "system" else [],
                    status=SubtaskStatus.PENDING,
                    result=None,
                ))

            # Validate DAG (detect cycles)
            if not TaskDecomposer._is_valid_dag(subtasks):
                logger.warning("LLM produced a cyclic dependency graph, falling back to normal chat")
                return None

            return TaskGraph(
                task_id=task_id,
                user_message=user_message,
                subtasks=subtasks,
            )

        except Exception as e:
            logger.error("Task decomposition failed, falling back to normal chat: %s", e)
            return None

    @staticmethod
    def _is_valid_dag(subtasks: List[Subtask]) -> bool:
        """Validate that the subtask graph is a valid DAG using Kahn's algorithm."""
        id_set = {s.id for s in subtasks}
        in_degree: dict[str, int] = {s.id: 0 for s in subtasks}
        adj: dict[str, list[str]] = {s.id: [] for s in subtasks}

        for s in subtasks:
            for dep_id in s.dependencies:
                if dep_id not in id_set:
                    continue
                adj[dep_id].append(s.id)
                in_degree[s.id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        visited = 0

        while queue:
            node = queue.pop(0)
            visited += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited == len(subtasks)
