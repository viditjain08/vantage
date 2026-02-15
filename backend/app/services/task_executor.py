import logging
import time
from typing import List
from fastapi import WebSocket

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import StructuredTool

from app.services.agent import AgentService
from app.schemas.task_graph import TaskGraph, Subtask, SubtaskStatus, SubtaskExecutor

logger = logging.getLogger("app.executor")


class TaskExecutor:
    """Manages execution lifecycle of a task graph."""

    def __init__(
        self,
        task_graph: TaskGraph,
        all_tools: List[StructuredTool],
        llm: BaseChatModel,
        chat_history: List[BaseMessage],
        websocket: WebSocket,
    ):
        self.graph = task_graph
        self.all_tools = all_tools
        self.llm = llm
        self.chat_history = chat_history
        self.websocket = websocket
        self._subtask_map: dict[str, Subtask] = {s.id: s for s in task_graph.subtasks}

    def get_ready_subtasks(self) -> List[Subtask]:
        """Return subtasks whose dependencies are all 'succeeded'."""
        ready = []
        for subtask in self.graph.subtasks:
            if subtask.status != SubtaskStatus.PENDING:
                continue
            deps_met = all(
                self._subtask_map[dep_id].status == SubtaskStatus.SUCCEEDED
                for dep_id in subtask.dependencies
                if dep_id in self._subtask_map
            )
            if deps_met:
                ready.append(subtask)
        return ready

    async def execute_ready_subtasks(self):
        """Find and execute all ready subtasks."""
        ready = self.get_ready_subtasks()
        for subtask in ready:
            if subtask.executor == SubtaskExecutor.SYSTEM:
                await self._execute_system_subtask(subtask)
            elif subtask.executor == SubtaskExecutor.USER and subtask.status == SubtaskStatus.PENDING:
                # Mark user subtask as in_progress so frontend shows input
                subtask.status = SubtaskStatus.IN_PROGRESS
                await self._send_status_update(subtask)

    async def _execute_system_subtask(self, subtask: Subtask):
        """Execute a single system subtask using a scoped LangGraph agent."""
        # Guard against re-execution from recursive execute_ready_subtasks calls
        if subtask.status != SubtaskStatus.PENDING:
            return
        subtask.status = SubtaskStatus.IN_PROGRESS
        logger.info("[Subtask Start] %s (id=%s, tools=%s)", subtask.name, subtask.id, subtask.tools)
        await self._send_status_update(subtask)

        try:
            # Filter tools to only those needed for this subtask
            if subtask.tools:
                scoped_tools = [t for t in self.all_tools if t.name in subtask.tools]
            else:
                scoped_tools = self.all_tools

            logger.info("  scoped tools: %s", [t.name for t in scoped_tools])

            # Build a scoped agent with only the relevant tools
            scoped_graph = AgentService.build_graph(self.llm, scoped_tools)

            # Build prompt with context from completed dependencies
            dep_context = self._build_dependency_context(subtask)
            prompt = (
                f"Execute this subtask: {subtask.name}\n"
                f"{subtask.description}\n\n"
                f"Context from completed prerequisites:\n{dep_context}\n\n"
                f"Format your response in markdown. When presenting structured data, comparisons, "
                f"lists of items with attributes, or costs/metrics, prefer using markdown tables."
            )

            logger.info("  prompt: %s", prompt[:300])

            input_state = {
                "messages": self.chat_history + [HumanMessage(content=prompt)]
            }
            t0 = time.time()
            final_state = await scoped_graph.ainvoke(input_state)
            result_text = final_state["messages"][-1].content

            subtask.status = SubtaskStatus.SUCCEEDED
            subtask.result = str(result_text)
            logger.info("[Subtask Done] %s | %.2fs | result: %s", subtask.name, time.time() - t0, str(result_text)[:300])
        except Exception as e:
            subtask.status = SubtaskStatus.FAILED
            subtask.result = f"Error: {str(e)}"
            logger.error("[Subtask Failed] %s | error: %s", subtask.name, e)

        await self._send_status_update(subtask)

        # If this subtask failed, propagate failure to dependents
        if subtask.status == SubtaskStatus.FAILED:
            await self._propagate_failure(subtask.id)

        # Check if more subtasks are now ready
        if not self.is_complete():
            await self.execute_ready_subtasks()

    async def handle_user_output(self, subtask_id: str, output: str):
        """Handle user-provided output for a user-type subtask."""
        subtask = self._subtask_map.get(subtask_id)
        if not subtask:
            logger.warning("User output for unknown subtask %s", subtask_id)
            return

        logger.info("[User Subtask Done] %s | output: %s", subtask.name, output[:200])
        subtask.status = SubtaskStatus.SUCCEEDED
        subtask.result = output
        await self._send_status_update(subtask)

        # Check if this completion unlocks more subtasks
        if not self.is_complete():
            await self.execute_ready_subtasks()

    def is_complete(self) -> bool:
        """Check if all subtasks are in a terminal state."""
        return all(
            s.status in (SubtaskStatus.SUCCEEDED, SubtaskStatus.FAILED)
            for s in self.graph.subtasks
        )

    async def _propagate_failure(self, failed_id: str):
        """Mark all transitive dependents of a failed subtask as failed."""
        to_fail = []
        for subtask in self.graph.subtasks:
            if subtask.status != SubtaskStatus.PENDING:
                continue
            if failed_id in subtask.dependencies:
                to_fail.append(subtask)

        for subtask in to_fail:
            subtask.status = SubtaskStatus.FAILED
            subtask.result = f"Skipped: dependency '{self._subtask_map[failed_id].name}' failed"
            await self._send_status_update(subtask)
            # Recursively propagate
            await self._propagate_failure(subtask.id)

    async def _send_status_update(self, subtask: Subtask):
        """Send a subtask status update to the frontend."""
        msg = {
            "type": "subtask_status_update",
            "task_id": self.graph.task_id,
            "subtask_id": subtask.id,
            "status": subtask.status.value,
            "result": subtask.result,
        }
        await self.websocket.send_json(msg)

        # If all complete, generate a final consolidated response for the chat
        if self.is_complete():
            logger.info("All subtasks complete for task %s — generating final summary", self.graph.task_id)
            summary = await self._build_final_response()
            await self.websocket.send_json({
                "type": "task_completed",
                "task_id": self.graph.task_id,
                "summary": summary,
            })

    def _build_dependency_context(self, subtask: Subtask) -> str:
        """Gather results from completed dependency subtasks."""
        parts = []
        for dep_id in subtask.dependencies:
            dep = self._subtask_map.get(dep_id)
            if dep and dep.result:
                parts.append(f"[{dep.name}]: {dep.result}")
        return "\n".join(parts) if parts else "No prerequisites."

    async def _build_final_response(self) -> str:
        """Synthesize a single final response from all subtask results using the LLM."""
        # Build context from all subtask results
        subtask_details = []
        for s in self.graph.subtasks:
            status = "SUCCEEDED" if s.status == SubtaskStatus.SUCCEEDED else "FAILED"
            subtask_details.append(f"[{status}] {s.name}: {s.result or '(no output)'}")
        all_results = "\n\n".join(subtask_details)

        prompt = (
            f"The user asked: {self.graph.user_message}\n\n"
            f"The following subtasks were executed to answer the request. "
            f"Synthesize a single, clear, final response for the user based on these results. "
            f"Do NOT list subtask names or mention that subtasks were executed. "
            f"Present the information as a direct answer to the user's original question. "
            f"Use markdown formatting with tables where appropriate.\n\n"
            f"Subtask results:\n{all_results}"
        )

        try:
            logger.info("[Final Summary LLM Request] Synthesizing final response")
            t0 = time.time()
            response = await self.llm.ainvoke(
                self.chat_history + [HumanMessage(content=prompt)]
            )
            summary = str(response.content)
            logger.info("[Final Summary LLM Response] %.2fs | %s", time.time() - t0, summary[:300])
            return summary
        except Exception as e:
            logger.error("Failed to generate final summary via LLM: %s", e)
            # Fallback: return a simple concatenation
            parts = []
            for s in self.graph.subtasks:
                icon = "OK" if s.status == SubtaskStatus.SUCCEEDED else "FAILED"
                parts.append(f"- [{icon}] {s.name}")
                if s.result:
                    parts.append(f"  {s.result}")
            return "Task complete.\n" + "\n".join(parts)
