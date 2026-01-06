# Virtual Developer Agent

A LangGraph-based multi-agent system that automates the development workflow from Jira ticket to Pull Request.

The agent works with a boilerplate React application (https://github.com/grinsteindavid/boilerplate-react-app) which it clones as a starting point.

## Overview

Virtual Developer Agent automates end-to-end delivery of Jira tasks:
- Fetches Jira ticket details and creates implementation plan
- Clones repository and creates feature branch
- Implements code changes using LLM
- Runs tests and iterates on failures
- Creates Pull Request on GitHub
- Updates Jira status and sends Discord notification

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                           │
│                                                                 │
│   ┌─────────────┐                                               │
│   │ Supervisor  │◄────────────────────────────┐                 │
│   └──────┬──────┘                             │                 │
│          │                                    │                 │
│   ┌──────┴──────┬──────────┬──────────┐      │                 │
│   ▼             ▼          ▼          ▼      │                 │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│ │ Planner │ │Implement│ │ Tester  │ │Reporter │───────────────┘│
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘                │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │  Tools: GitHub | Jira | Discord | Filesystem                ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Responsibility |
|-------|----------------|
| **Supervisor** | Routes workflow to appropriate specialist agent |
| **Planner** | Fetches Jira ticket, creates implementation plan |
| **Implementer** | Clones repo, creates branch, writes code |
| **Tester** | Runs test suite, analyzes failures |
| **Reporter** | Creates PR, updates Jira, sends Discord notification |

### Components

- **`src/agents/`** - LangGraph agent implementations
- **`src/tools/`** - LangChain tools (GitHub, Jira, Discord, Filesystem)
- **`src/clients/`** - API client wrappers
- **`src/api/`** - Optional FastAPI for webhook triggers
- **`src/db/`** - Redis checkpointer for state persistence

## Prerequisites

- **Docker & Docker Compose**
- **OpenAI API Key** (or Anthropic)
- **GitHub**: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`
- **Jira**: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `JIRA_PROJECT`
- **Discord**: `DISCORD_WEBHOOK_URL`

## Quick Start

1. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Build and start**:
   ```bash
   make setup
   ```

3. **Run unit tests**:
   ```bash
   make test
   ```

4. **Run workflow for a ticket**:
   ```bash
   make run TICKET=DP-123
   ```

## Configuration

Environment variables (`.env`):

```bash
# LLM
OPENAI_API_KEY=your_openai_api_key

# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_owner
GITHUB_REPO=boilerplate-react-app

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@example.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT=YOURPROJ

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Redis (for state persistence)
REDIS_URL=redis://localhost:6379/0

# Workflow (alternative to --ticket flag)
TICKET=DP-123
```

## Make Commands

```bash
make help              # Show all commands

# Development
make setup             # Build and start containers
make dev               # Start with hot-reload
make down              # Stop containers
make logs              # View logs

# Testing (all via Docker)
make test              # Run unit tests
make test-unit         # Run unit tests (alias)
make test-integration  # Run integration tests
make test-coverage     # Tests with coverage

# Workflow
make run TICKET=DP-123 # Run workflow for ticket

# Cleanup
make clean             # Remove containers and cache
```

## How It Works

1. **Planning**: Fetches Jira ticket details, creates step-by-step implementation plan
2. **Implementation**: Clones target repo, creates branch, implements code using LLM
3. **Testing**: Runs Jest tests, iterates on failures (max 3 attempts)
4. **Reporting**: Creates/updates PR, transitions Jira to "In Review", sends Discord summary

### Data Flow

```
Input: TICKET=DP-123
    │
    ▼
Supervisor → Planner (fetch Jira, create plan)
    │
    ▼
Supervisor → Implementer (clone, branch, code)
    │
    ▼
Supervisor → Tester (run tests, fix failures)
    │
    ▼
Supervisor → Reporter (PR, Jira, Discord)
    │
    ▼
Output: PR URL, Jira transitioned, Discord notified
```

## Project Structure

```
virtual-dev-agent/
├── src/
│   ├── agents/          # LangGraph agents
│   │   ├── graph.py     # Workflow graph
│   │   ├── supervisor.py
│   │   ├── planner.py
│   │   ├── implementer.py
│   │   ├── tester.py
│   │   └── reporter.py
│   ├── tools/           # LangChain tools
│   ├── clients/         # API clients
│   ├── api/             # FastAPI (optional)
│   └── db/              # Redis checkpointer
├── tests/
│   ├── unit/            # Unit tests (mocked)
│   └── integration/     # Integration tests
├── compose/             # Docker Compose files
├── docker/              # Dockerfiles
└── docs/                # Architecture docs
```

## Testing

- **Unit tests**: All dependencies mocked, no network calls
- **Integration tests**: Require API keys, test full workflow

```bash
make test              # Unit tests in Docker (44 tests)
make test-integration  # Integration tests (requires API keys)
make test-coverage     # Tests with coverage report
```

## State Persistence

Uses Redis for LangGraph checkpointing:
- Resume interrupted workflows
- Inspect state at any point
- Support concurrent workflows

Redis is automatically started via Docker Compose.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing `.env` | `cp .env.example .env` and fill in values |
| Tests fail | Check mock implementations in `tests/mocks/` |
| Redis connection error | Ensure Redis is running: `make dev` |
| Jira/GitHub errors | Verify API tokens and permissions |
| LLM errors | Check `OPENAI_API_KEY` is valid |

## Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/IMPLEMENTATION_PLAN.md` - Implementation details
- `docs/TOOLS_MAPPING.md` - MCP to LangGraph tool mapping
- `docs/TESTING_STRATEGY.md` - Testing approach
- `docs/FILE_STRUCTURE.md` - Complete file listing

## Example Screenshots

## Prompt for creating the jira ticket description
<img width="665" height="455" alt="image" src="https://github.com/user-attachments/assets/5836d2d9-9f64-46e5-9b70-2c77ddeb6314" />

## Jira ticket
<img width="623" height="590" alt="image" src="https://github.com/user-attachments/assets/1b0bc254-8150-49b4-8b56-0b16724aea1e" />
<img width="638" height="587" alt="image" src="https://github.com/user-attachments/assets/cff47f36-7554-4b9a-8b61-a11515f3c52a" />
<img width="645" height="430" alt="image" src="https://github.com/user-attachments/assets/bfda1c0c-a1ac-485c-b1da-2d74125ed6ee" />

## First commits and Pull request
<img width="756" height="529" alt="image" src="https://github.com/user-attachments/assets/4e8e03d8-b168-4cf0-bfb8-11ebdc241c20" />

## It sends a comment if PR exists and commits were sent as well
<img width="770" height="447" alt="image" src="https://github.com/user-attachments/assets/db4a3adb-91e5-463f-b4e6-2ae39b61d378" />

## Jira comment after sending Pull request
<img width="630" height="613" alt="image" src="https://github.com/user-attachments/assets/959a7e71-0240-47e6-8183-111a918ed0a9" />

## Discord alert after sending Pull request
<img width="838" height="633" alt="image" src="https://github.com/user-attachments/assets/7684c8ed-2a75-4183-b332-da3565a25b5a" />

# Vercel auto deploy integration in the boilerplate repo
<img width="849" height="629" alt="image" src="https://github.com/user-attachments/assets/a35f6cfc-8e1e-460d-a89f-03b197bc9fae" />

