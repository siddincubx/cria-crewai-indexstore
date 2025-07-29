# CRIA Hackathon Project

This repository contains a comprehensive project with two main components: an AI-powered Impact Analysis system (CRIA CrewAI) and a Training Program Management System. Both systems work together to provide intelligent analysis of organizational data including JIRA tickets, Confluence documentation, and codebase insights.

## 🏗️ Project Architecture

```
hackathon_cria/
├── cria_crew/              # AI Impact Analysis System (CrewAI)
├── training-management-system/  # Full-Stack Training Management App
└── postgres.yaml           # Shared PostgreSQL database setup
```

## 🔧 Components Overview

### 1. CRIA CrewAI System (`cria_crew/`)
An intelligent multi-agent AI system that analyzes organizational data using specialized agents:
- **JIRA Specialist**: Semantic search through JIRA tickets
- **Confluence Specialist**: RAG-based documentation search
- **Codebase Specialist**: Code analysis and pattern detection
- **Reporting Analyst**: Comprehensive report generation

### 2. Training Management System (`training-management-system/`)
A full-stack Next.js application for managing corporate training programs:
- Employee enrollment and management
- Training session tracking
- Attendance monitoring
- Certificate generation
- Feedback collection

---

## 🚀 Quick Start

### Prerequisites

Before running any component, ensure you have:

- **Python 3.11-3.13** (for CRIA CrewAI)
- **UV package manager** (recommended for Python dependencies)

## 🤖 CRIA CrewAI System Setup

### Installation

1. **Navigate to the CRIA directory**:
   ```bash
   cd cria_crew
   ```

2. **Install UV package manager** (if not already installed):
   ```bash
   pip install uv
   ```

3. **Install dependencies**:
   ```bash
   # Using UV (recommended)
   uv sync

   # Or using crewai CLI
   crewai install
   ```

### Environment Configuration

1. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure required environment variables** in `.env`:

   ```env
   # AI Models
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   CLAUDE_API_KEY=your_claude_api_key_here

   # JIRA Configuration
   BASE_URL=https://your-domain.atlassian.net
   USER_EMAIL=your-email@company.com
   API_TOKEN=your_jira_api_token

   # Confluence Configuration
   CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
   CONFLUENCE_TOKEN=your_confluence_token

   # Vector Database (Pinecone)
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=jira-issues
   PINECONE_CONFLUENCE_INDEX=confluence-pages


### Data Indexing Setup

Before using the AI agents, you need to index your data:

### Running CRIA CrewAI

#### Option 1: Command Line Interface
Uncomment the crewai block in `main.py`
```bash
# Run with default crew configuration
crewai run

OR 

uvx crewai run

# This will generate a report.md file with analysis results
```

#### Option 2: Web API Server
```bash
# Start FastAPI server
uv run src/cria_crew/main.py

# Or with custom host/port
uv run src/cria_crew/main.py --host 0.0.0.0 --port 8080
```

API endpoints:
- `POST /api/query` - Submit analysis queries
- `GET /health` - Health check

#### Option 3: Panel Interface

```bash
git checkout feature/panel-ui

# Launch interactive web interface
uv run src/cria_crew/main.py

```

### Training Management System Features

#### For HR Administrators:
- Create and manage training programs
- Set enrollment limits and waitlists
- Track attendance and completion rates
- Generate certificates
- Monitor system analytics

#### For Employees:
- Browse available training programs
- Enroll in training sessions
- Track attendance and progress
- Download certificates
- Provide feedback

---

## 🛠️ Development

### Project Structure

#### CRIA CrewAI (`cria_crew/`)
```
cria_crew/
├── src/cria_crew/
│   ├── config/           # Agent and task configurations
│   ├── tools/            # Custom AI tools
│   ├── data_models/      # Pydantic schemas
│   ├── crew.py          # Main crew orchestration
│   ├── main.py          # FastAPI server
├── scripts/             # Data loading and sync scripts
├── notebooks/           # Jupyter notebooks for setup
└── knowledge/           # Knowledge base files
```

#### CRIA CrewAI:
1. **New Agent**: Add to `src/cria_crew/config/agents.yaml`
2. **New Task**: Add to `src/cria_crew/config/tasks.yaml`
3. **New Tool**: Create in `src/cria_crew/tools/`
4. **Custom Logic**: Modify `src/cria_crew/crew.py`

### Health Checks
- **CRIA API**: `GET /health`

**Built with ❤️ by Sir Learns-A-Lot**
