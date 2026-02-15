# Vantage Agent

An intelligent AI agent platform that enables users to create custom AI assistants with specialized capabilities through the Model Context Protocol (MCP).

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd vantage

# Start database
make db-start

# Start backend (in one terminal)
make backend

# Start frontend (in another terminal)
make frontend
```

Visit `http://localhost:3000` to access the application.

For detailed setup instructions, see [SETUP.md](SETUP.md).

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Capabilities

- **🤖 Multi-LLM Support**
  - OpenAI (Direct API, Azure, AWS Bedrock)
  - Claude/Anthropic (Direct API, Azure, AWS Bedrock)
  - Flexible provider configuration
  - Temperature and parameter control

- **🔧 MCP Integration**
  - Connect to external tools via Model Context Protocol
  - Support for SSE, HTTP, and STDIO server types
  - Dynamic tool discovery and registration
  - Real-time tool execution

- **📊 Task Decomposition & Orchestration**
  - Automatic breakdown of complex tasks into subtasks
  - DAG (Directed Acyclic Graph) execution planning
  - Parallel and sequential task execution
  - System and user executor types
  - **Human-in-the-loop** task delegation
  - **User approval workflow** for critical tasks
  - Progress tracking and visualization
  - Dependency management

- **💬 Context Management & Compression**
  - Intelligent conversation history compression
  - **FAISS-based semantic search** for context retrieval
  - Vector similarity search for relevant context
  - Token counting and optimization
  - Automatic context window management
  - Relevant context extraction from long conversations
  - System message preservation

- **✍️ Prompt Enhancement**
  - **AI-powered system prompt optimization**
  - LLM-based prompt improvement suggestions
  - Best practice integration
  - Automatic structuring and formatting
  - Task breakdown instructions
  - Context-aware prompt refinement

- **🔄 Real-time Communication**
  - WebSocket-based chat interface
  - Streaming responses
  - Connection status monitoring
  - Error handling and recovery

- **📁 Category System**
  - Create specialized agent categories
  - Custom system prompts
  - LLM configuration per category
  - MCP server associations

- **🗂️ Registry Service**
  - Pre-configured MCP server catalog (40+ servers)
  - LLM-powered server suggestions
  - Category-based recommendations with keyword fallback
  - Extensible server registry
  - Support for GitHub, GitLab, PostgreSQL, AWS, Azure, GCP, and more

- **🔍 Observability & Tracing**
  - **Phoenix/Arize integration** for LLM tracing
  - Real-time monitoring of LLM calls
  - Token usage tracking
  - Latency and performance metrics
  - Request/response logging
  - Error tracking and debugging

- **🔐 Resource Configuration**
  - Multi-cloud resource support (AWS, Azure, GCP)
  - Kubernetes cluster integration
  - Secure credential management
  - Environment-specific configurations
  - Header-based authentication for MCP servers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + React)                │
│  • Chat Interface  • Category Management  • Tool Discovery  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer                                            │  │
│  │  • Categories  • Chat  • Tools  • Registry           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Layer                                        │  │
│  │  • Agent  • LLM Factory  • Task Decomposer           │  │
│  │  • Task Executor  • Context  • Prompt Enhancer       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Layer                                           │  │
│  │  • PostgreSQL  • SQLAlchemy  • Alembic               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
┌────────────────────────▼────────────────────────────────────┐
│                    External MCP Servers                      │
│  • GitHub  • Postgres  • Web Search  • Custom Tools         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI - Modern web framework
- SQLAlchemy - ORM and database toolkit
- Alembic - Database migrations
- LangChain - LLM orchestration
- LangGraph - Agent workflow management
- MCP - Model Context Protocol client
- FAISS - Vector similarity search
- Pydantic - Data validation

**Frontend:**
- Next.js 16 - React framework
- TypeScript - Type safety
- TailwindCSS - Utility-first CSS
- React Query - Server state management
- WebSocket - Real-time communication

**Database:**
- PostgreSQL 15+ - Relational database

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Complete installation and setup guide
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Comprehensive feature documentation
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when running)

## 🛠️ Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your configuration
```

For detailed instructions, see [SETUP.md](SETUP.md).

## 🎯 Usage

### Creating a Category

```python
# Via API
POST /api/v1/categories
{
  "name": "Data Analysis",
  "system_prompt": "You are a data analysis expert...",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "llm_provider_type": "direct"
}
```

### Adding MCP Server

```python
# Via API
POST /api/v1/mcp-servers
{
  "name": "GitHub Tools",
  "url": "https://mcp.github.com/server",
  "type": "sse",
  "category_id": 1
}
```

### Chat with Agent

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/chat/1');

ws.send(JSON.stringify({
  type: 'user_message',
  content: 'Analyze the sales data from last quarter'
}));

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

## 🧪 Testing

### Quick Test Commands (Makefile)

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Generate HTML coverage report
make test-coverage-html

# Run specific test file
make test-file file='tests/test_registry.py'

# Re-run only failed tests
make test-failed
```

### Backend Tests (Direct)

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_prompt_enhancer.py

# Run specific test
pytest tests/test_llm_factory.py::TestLLMFactory::test_create_openai_direct
```

### Test Coverage

**Overall Coverage: 74%** ✅ (31/31 tests passing)

Detailed coverage:
- ✅ Prompt Enhancer Service (100%)
- ✅ Registry Service (97%)
- ✅ Task Decomposer (90%)
- ✅ Context Service (60%)
- ✅ LLM Factory (58%)
- ✅ MCP Client (59%)

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing documentation.

### Frontend Tests

```bash
cd frontend
npm test
```

## 📦 Project Structure

```
vantage/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Configuration
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI application
│   ├── alembic/              # Database migrations
│   ├── tests/                # Unit tests
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── lib/              # Utilities
│   └── package.json          # Node dependencies
├── SETUP.md                  # Setup guide
├── DOCUMENTATION.md          # Complete documentation
└── README.md                 # This file
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow existing code style
- Update documentation
- Ensure all tests pass
- Add type hints (Python) / types (TypeScript)

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent workflows
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Next.js](https://nextjs.org/) - React framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - Tool integration standard

## 📞 Support

- 📖 [Documentation](DOCUMENTATION.md)
- 🐛 [Issue Tracker](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)

## 🗺️ Roadmap

### Current Version (1.0.0)
- ✅ Multi-LLM provider support
- ✅ MCP integration
- ✅ Task decomposition
- ✅ Context compression
- ✅ Prompt enhancement
- ✅ WebSocket chat
- ✅ Comprehensive tests

### Planned Features
- 🔐 Authentication and authorization
- 👥 Multi-tenancy support
- 📊 Analytics dashboard
- 🔌 Plugin system
- 🎤 Voice interface
- 📱 Mobile application
- 🌐 Multi-language support
- 🔍 Advanced search capabilities

---

**Built with ❤️ using FastAPI, Next.js, and LangChain**