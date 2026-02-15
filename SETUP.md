# Vantage Agent - Setup Guide

This guide will help you set up and run the Vantage Agent application locally.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software
- **Python 3.12+** - Backend runtime
- **Node.js 18+** and **npm** - Frontend runtime
- **PostgreSQL 15+** - Database
- **Git** - Version control

### Optional Tools
- **Make** - For using Makefile commands

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vantage
```

### 2. Backend Setup

#### Create Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Set Up PostgreSQL Database

**macOS (Using Homebrew)**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian (Using apt)**
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql
```

**Windows**
1. Download PostgreSQL 15+ from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the setup wizard
3. Start PostgreSQL service from Services panel or pgAdmin

#### Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE vantage;

# Create user (optional)
CREATE USER vantage_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vantage TO vantage_user;

# Exit psql
\q
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env  # If example exists, otherwise create new file
```

Add the following configuration to `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vantage
```

#### Run Database Migrations

```bash
make migrate
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Configuration

### Backend Configuration

The backend configuration is managed through:
- **Environment variables** (`.env` file)
- **Settings** (`backend/app/core/config.py`)

Key configuration options:
- `DATABASE_URL` - PostgreSQL connection string
- `API_V1_STR` - API version prefix (default: `/api/v1`)
- LLM provider credentials (OpenAI, Azure, Claude, AWS)

### Frontend Configuration

Frontend configuration is in `frontend/next.config.ts` and environment variables.

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Using Make Commands (Recommended)

The project includes a Makefile for easy management:

```bash
# Start PostgreSQL
make db-start

# Check database status
make db-status

# Start backend (in one terminal)
make backend

# Start frontend (in another terminal)
make frontend

# Stop database
make db-stop
```

### Manual Startup

#### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

#### Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_prompt_enhancer.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_prompt_enhancer.py::TestPromptEnhancer::test_enhance_success
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Troubleshooting

### Common Issues

#### Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct.

#### Port Already in Use
```
Error: listen EADDRINUSE: address already in use :::8000
```
**Solution**: Kill the process using the port or use a different port.

#### Module Not Found
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure virtual environment is activated and dependencies are installed.

#### Migration Errors
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'
```
**Solution**: Reset migrations or check alembic version history.

### Getting Help

- Check the [Documentation](DOCUMENTATION.md)
- Review logs in `backend/logs/` and `postgres.log`
- Open an issue on GitHub

## Next Steps

After setup, refer to:
- [DOCUMENTATION.md](DOCUMENTATION.md) - Complete feature documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Architecture Guide](ARCHITECTURE.md) - System architecture (if available)

