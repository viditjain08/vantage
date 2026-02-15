# Backend Tests

This directory contains unit and integration tests for the Vantage Agent backend.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_prompt_enhancer.py  # Prompt enhancement tests
├── test_llm_factory.py      # LLM factory tests
├── test_registry.py         # Registry service tests
├── test_task_decomposer.py  # Task decomposition tests
├── test_context_service.py  # Context management tests
└── README.md                # This file
```

## Running Tests

### Run All Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Run Specific Test File

```bash
pytest tests/test_prompt_enhancer.py
```

### Run Specific Test

```bash
pytest tests/test_llm_factory.py::TestLLMFactory::test_create_openai_direct
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run with Verbose Output

```bash
pytest -v
```

### Run Only Fast Tests

```bash
pytest -m "not slow"
```

## Test Categories

Tests are marked with the following markers:

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

## Writing Tests

### Unit Test Example

```python
import pytest
from app.services.my_service import MyService

class TestMyService:
    """Test suite for MyService."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = MyService.do_something()
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await MyService.do_something_async()
        assert result is not None
```

### Using Fixtures

```python
def test_with_mock_db(mock_db_session):
    """Test using mock database session."""
    # mock_db_session is provided by conftest.py
    result = my_function(mock_db_session)
    assert result is not None
```

### Mocking External Services

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mocked_llm():
    """Test with mocked LLM."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = "mocked response"
    
    with patch('app.services.llm_factory.ChatOpenAI', return_value=mock_llm):
        result = await my_function()
        assert result == "mocked response"
```

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Service Layer**: > 90%
- **API Endpoints**: > 75%
- **Models**: > 70%

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Scheduled daily runs

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:
1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt -r requirements-dev.txt`
3. You're running from the backend directory

### Database Errors

Tests use an in-memory SQLite database. If you encounter database errors:
1. Check that `aiosqlite` is installed
2. Verify fixtures in `conftest.py` are working
3. Ensure test database is properly cleaned up between tests

### Async Test Errors

For async test issues:
1. Ensure `pytest-asyncio` is installed
2. Mark async tests with `@pytest.mark.asyncio`
3. Check `pytest.ini` has `asyncio_mode = auto`

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external services and APIs
3. **Fixtures**: Use fixtures for common setup
4. **Naming**: Use descriptive test names
5. **Documentation**: Add docstrings to test classes and methods
6. **Assertions**: Use specific assertions with clear messages
7. **Coverage**: Aim for high coverage but focus on meaningful tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

