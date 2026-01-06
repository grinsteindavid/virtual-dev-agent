# Virtual Developer Agent - LangGraph Architecture

## Overview

This document describes the architecture for converting the Virtual Developer Agent from an MCP-based system to a LangGraph multi-agent system. The new architecture replaces the separate MCP servers (Discord, GitHub, Jira) with LangChain tools orchestrated by LangGraph agents.

## Current Architecture (MCP-based)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Compose                                │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │ Discord MCP  │    │ GitHub MCP   │    │  Jira MCP    │           │
│  │  Port 3001   │    │  Port 3002   │    │  Port 3003   │           │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘           │
│         │                   │                   │                    │
│         └─────────────┬─────┴─────────────┬─────┘                    │
│                       │   HTTP JSON-RPC   │                          │
│                       ▼                   ▼                          │
│              ┌────────────────────────────────┐                      │
│              │      Gemini CLI (Developer)    │                      │
│              │    System Prompt: GEMINI.md    │                      │
│              │    Task: plan.md               │                      │
│              └────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Current Components
- **Gemini CLI**: AI engine running with system instructions
- **MCP Servers**: Separate Node.js services for each integration
- **Transport**: Express + StreamableHTTPServerTransport (JSON-RPC)
- **Communication**: HTTP requests between containers

## New Architecture (LangGraph-based)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Single Python Process                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI (Optional)                          │ │
│  │                      Port 5000                                 │ │
│  └──────────────────────────┬─────────────────────────────────────┘ │
│                             │                                        │
│                             ▼                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   LangGraph Workflow                           │ │
│  │                                                                │ │
│  │   ┌─────────────┐                                              │ │
│  │   │ Supervisor  │◄────────────────────────────────┐            │ │
│  │   └──────┬──────┘                                 │            │ │
│  │          │                                        │            │ │
│  │   ┌──────┴──────┬──────────┬──────────┐          │            │ │
│  │   ▼             ▼          ▼          ▼          │            │ │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │            │ │
│  │ │ Planner │ │Implement│ │ Tester  │ │Reporter │──┘            │ │
│  │ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘               │ │
│  │      │           │           │           │                     │ │
│  └──────┼───────────┼───────────┼───────────┼─────────────────────┘ │
│         │           │           │           │                        │
│         ▼           ▼           ▼           ▼                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     LangChain Tools                            │ │
│  │                                                                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │  GitHub  │  │   Jira   │  │ Discord  │  │Filesystem│       │ │
│  │  │  Tools   │  │  Tools   │  │  Tools   │  │  Tools   │       │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      API Clients                               │ │
│  │                                                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │GitHubClient  │  │ JiraClient   │  │DiscordClient │         │ │
│  │  │  (httpx)     │  │  (httpx)     │  │  (httpx)     │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

### Supervisor Agent
- **Purpose**: Routes workflow to the appropriate agent based on current state
- **Input**: Current `GraphState`
- **Output**: Route decision (`planner`, `implementer`, `tester`, `reporter`, `done`)
- **Logic**: Evaluates state to determine next step in workflow

### Planner Agent
- **Purpose**: Fetches Jira ticket details and creates implementation plan
- **Tools Used**: `get_jira_issue`, `get_jira_transitions`
- **Output**: `jira_details`, `implementation_plan`, `branch_name`

### Implementer Agent
- **Purpose**: Clones repo, creates branch, implements code changes
- **Tools Used**: `clone_repo`, `create_branch`, `read_file`, `write_file`, `run_command`
- **Output**: `code_changes`, updated files in working directory

### Tester Agent
- **Purpose**: Writes tests, runs test suite, iterates on failures
- **Tools Used**: `run_tests`, `read_file`, `write_file`
- **Output**: `test_results` with pass/fail counts

### Reporter Agent
- **Purpose**: Creates PR, updates Jira, notifies Discord
- **Tools Used**: `commit_and_push`, `create_pr`, `transition_jira`, `add_jira_comment`, `send_discord`
- **Output**: `pr_url`, Jira transitioned, Discord notified

## Data Flow

```
1. Input: jira_ticket_id
         │
         ▼
2. Supervisor → Planner
         │
         ▼
3. Planner fetches Jira details, creates plan
         │
         ▼
4. Supervisor → Implementer
         │
         ▼
5. Implementer clones repo, creates branch, writes code
         │
         ▼
6. Supervisor → Tester
         │
         ▼
7. Tester runs tests, fixes failures (may loop)
         │
         ▼
8. Supervisor → Reporter (if tests pass)
         │
         ▼
9. Reporter creates PR, updates Jira, notifies Discord
         │
         ▼
10. Supervisor → Done
```

## State Management

### GraphState (TypedDict)
```python
class GraphState(TypedDict, total=False):
    # Input
    jira_ticket_id: str
    
    # Jira data
    jira_details: dict
    
    # Planning
    branch_name: str
    implementation_plan: str
    
    # Implementation
    repo_path: str
    code_changes: list[dict]
    
    # Testing
    test_results: dict
    test_iterations: int
    
    # Reporting
    pr_url: str
    pr_number: int
    
    # Workflow control
    route: str
    status: str  # pending, planning, implementing, testing, reporting, done, failed
    error: str | None
```

## Key Differences from MCP Architecture

| Aspect | MCP (Old) | LangGraph (New) |
|--------|-----------|-----------------|
| **Runtime** | 4 Docker containers | Single Python process |
| **Communication** | HTTP JSON-RPC | Direct function calls |
| **AI Engine** | Gemini CLI | LangChain + OpenAI/Anthropic |
| **Tool Definition** | MCP `server.tool()` | LangChain `@tool` decorator |
| **State** | Files (plan.md) | LangGraph `GraphState` |
| **Orchestration** | System prompt | LangGraph supervisor routing |
| **Session** | MCP session headers | LangGraph checkpointer |

## Benefits of New Architecture

1. **Simpler Deployment**: Single process vs. 4 containers
2. **Easier Testing**: Direct function calls, mock-friendly
3. **Better Observability**: Single log stream, traceable state
4. **Type Safety**: Pydantic models, TypedDict state
5. **Extensibility**: Add agents/tools without new services
6. **Debuggability**: Step through Python code directly
