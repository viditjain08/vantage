from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SubtaskExecutor(str, Enum):
    SYSTEM = "system"
    USER = "user"


class Subtask(BaseModel):
    id: str
    name: str
    description: str
    executor: SubtaskExecutor
    dependencies: list[str]  # subtask IDs
    tools: list[str] = []  # tool names needed for this subtask
    status: SubtaskStatus = SubtaskStatus.PENDING
    result: Optional[str] = None


class TaskGraph(BaseModel):
    task_id: str
    user_message: str
    subtasks: list[Subtask]


# Models for LLM structured output
class SubtaskSpec(BaseModel):
    name: str
    description: str
    executor: str  # "system" or "user"
    depends_on: list[str] = []  # names of other subtasks
    tools: list[str] = []  # tool names needed (for system executor)


class DecompositionResponse(BaseModel):
    should_decompose: bool
    reasoning: str
    subtasks: list[SubtaskSpec] = []
