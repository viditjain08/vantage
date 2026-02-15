"""
Unit tests for the TaskDecomposer service.

Tests task decomposition logic and DAG validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.task_decomposer import TaskDecomposer
from app.schemas.task_graph import DecompositionResponse, SubtaskSpec, Subtask, SubtaskStatus


class TestTaskDecomposer:
    """Test suite for TaskDecomposer class."""

    @pytest.mark.asyncio
    async def test_maybe_decompose_returns_none_for_simple_question(self):
        """Test that simple questions don't get decomposed."""
        # Arrange
        mock_category = MagicMock()
        mock_category.llm_provider = "openai"
        mock_category.llm_model = "gpt-4"
        mock_category.llm_provider_type = "direct"
        mock_category.llm_api_key = "test-key"
        mock_category.llm_endpoint = None
        mock_category.llm_api_version = None
        mock_category.llm_deployment_name = None
        mock_category.llm_region = None
        
        mock_llm = AsyncMock()
        mock_response = DecompositionResponse(
            should_decompose=False,
            reasoning="This is a simple question",
            subtasks=[]
        )
        
        with patch('app.services.task_decomposer.LLMFactory.create_llm', return_value=mock_llm):
            mock_llm.with_structured_output.return_value.ainvoke.return_value = mock_response
            
            # Act
            result = await TaskDecomposer.maybe_decompose(
                user_message="What is Python?",
                chat_history=[],
                category=mock_category,
                available_tools=[]
            )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_maybe_decompose_creates_task_graph(self):
        """Test that complex tasks get decomposed into task graph."""
        # Arrange
        mock_category = MagicMock()
        mock_category.llm_provider = "openai"
        mock_category.llm_model = "gpt-4"
        mock_category.llm_provider_type = "direct"
        mock_category.llm_api_key = "test-key"
        mock_category.llm_endpoint = None
        mock_category.llm_api_version = None
        mock_category.llm_deployment_name = None
        mock_category.llm_region = None

        mock_response = DecompositionResponse(
            should_decompose=True,
            reasoning="This requires multiple steps",
            subtasks=[
                SubtaskSpec(
                    name="Step 1",
                    description="First step",
                    executor="system",
                    depends_on=[],
                    tools=["tool1"]
                ),
                SubtaskSpec(
                    name="Step 2",
                    description="Second step",
                    executor="system",
                    depends_on=["Step 1"],
                    tools=["tool2"]
                )
            ]
        )

        # Create mock structured output
        mock_structured = AsyncMock()
        mock_structured.ainvoke.return_value = mock_response

        # Create mock LLM
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch('app.services.task_decomposer.LLMFactory.create_llm', return_value=mock_llm):
            # Act
            result = await TaskDecomposer.maybe_decompose(
                user_message="Deploy the application",
                chat_history=[],
                category=mock_category,
                available_tools=[{"name": "tool1", "description": "Tool 1"}]
            )

        # Assert
        assert result is not None
        assert len(result.subtasks) == 2
        assert result.subtasks[0].name == "Step 1"
        assert result.subtasks[1].name == "Step 2"
        assert result.subtasks[1].dependencies[0] == result.subtasks[0].id

    @pytest.mark.asyncio
    async def test_is_valid_dag_detects_cycle(self):
        """Test that cyclic dependencies are detected."""
        # Create subtasks with circular dependency
        subtask1 = Subtask(
            id="1",
            name="Task 1",
            description="First task",
            executor="system",
            dependencies=["2"],  # Depends on task 2
            tools=[],
            status=SubtaskStatus.PENDING
        )
        subtask2 = Subtask(
            id="2",
            name="Task 2",
            description="Second task",
            executor="system",
            dependencies=["1"],  # Depends on task 1 (cycle!)
            tools=[],
            status=SubtaskStatus.PENDING
        )
        
        # Act
        is_valid = TaskDecomposer._is_valid_dag([subtask1, subtask2])
        
        # Assert
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_is_valid_dag_accepts_valid_dag(self):
        """Test that valid DAG is accepted."""
        subtask1 = Subtask(
            id="1",
            name="Task 1",
            description="First task",
            executor="system",
            dependencies=[],
            tools=[],
            status=SubtaskStatus.PENDING
        )
        subtask2 = Subtask(
            id="2",
            name="Task 2",
            description="Second task",
            executor="system",
            dependencies=["1"],
            tools=[],
            status=SubtaskStatus.PENDING
        )
        
        # Act
        is_valid = TaskDecomposer._is_valid_dag([subtask1, subtask2])
        
        # Assert
        assert is_valid is True

