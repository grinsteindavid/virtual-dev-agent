# Implementation Plan

This document outlines the step-by-step plan to convert the Virtual Developer Agent from MCP-based architecture to LangGraph.

## Phase 1: Project Setup

### 1.1 Create Python Project Structure

```
src/
├── __init__.py
├── config.py              # Environment configuration
├── logger.py              # Logging setup
├── clients/               # API clients
├── tools/                 # LangChain tools
├── agents/                # LangGraph agents
└── api/                   # FastAPI (optional)
```

### 1.2 Create `pyproject.toml`

```toml
[project]
name = "virtual-dev-agent"
version = "0.1.0"
description = "LangGraph-based virtual developer agent"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
api = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
]
```

### 1.3 Create Configuration Module

**File**: `src/config.py`
- Load environment variables
- Validate required vars
- Export typed config object

### 1.4 Create Logger Module

**File**: `src/logger.py`
- Configure structured logging
- File + console output
- Match existing Winston format

---

## Phase 2: API Clients

Create thin wrapper classes for each external API.

### 2.1 GitHub Client

**File**: `src/clients/github_client.py`

Methods:
- `get_repo(owner, repo) -> dict`
- `create_issue(owner, repo, title, body) -> dict`
- `create_pull_request(owner, repo, title, body, head, base) -> dict`
- `create_pr_comment(owner, repo, pr_number, body) -> dict`
- `list_pull_requests(owner, repo, state, limit) -> list[dict]`

### 2.2 Jira Client

**File**: `src/clients/jira_client.py`

Methods:
- `get_issue(issue_key) -> dict`
- `list_issues(status, limit) -> list[dict]`
- `add_comment(issue_key, comment) -> dict`
- `get_transitions(issue_key) -> list[dict]`
- `transition_issue(issue_key, transition_id) -> dict`
- `download_attachments(issue_key, types, dest_dir) -> list[str]`

### 2.3 Discord Client

**File**: `src/clients/discord_client.py`

Methods:
- `send_message(content, username) -> dict`
- `send_embed(title, description, color, url) -> dict`
- `send_notification(type, message, details) -> dict`

---

## Phase 3: LangChain Tools

Wrap clients as LangChain tools with Pydantic schemas.

### 3.1 GitHub Tools

**File**: `src/tools/github.py`

Tools:
- `get_repo_info`
- `create_issue`
- `create_pull_request`
- `create_pr_comment`
- `list_pull_requests`

### 3.2 Jira Tools

**File**: `src/tools/jira.py`

Tools:
- `get_jira_issue`
- `list_jira_issues`
- `add_jira_comment`
- `get_jira_transitions`
- `transition_jira_issue`
- `download_jira_attachments`

### 3.3 Discord Tools

**File**: `src/tools/discord.py`

Tools:
- `send_discord_message`
- `send_discord_embed`
- `send_discord_notification`

### 3.4 Filesystem Tools

**File**: `src/tools/filesystem.py`

Tools:
- `read_file`
- `write_file`
- `run_command`

---

## Phase 4: Agent State

### 4.1 Define State Types

**File**: `src/agents/state.py`

```python
class GraphState(TypedDict, total=False):
    jira_ticket_id: str
    jira_details: dict
    branch_name: str
    implementation_plan: str
    repo_path: str
    code_changes: list[dict]
    test_results: dict
    test_iterations: int
    pr_url: str
    pr_number: int
    route: str
    status: str
    error: str | None

@dataclass
class AgentState:
    # Mirror of GraphState for agent internal use
    ...
    
    @classmethod
    def from_graph_state(cls, state: dict) -> "AgentState":
        ...
```

---

## Phase 5: Agents

### 5.1 Supervisor Agent

**File**: `src/agents/supervisor.py`

- Routes to: `planner`, `implementer`, `tester`, `reporter`, or `done`
- Uses LLM to evaluate current state
- Returns route decision with confidence

### 5.2 Planner Agent

**File**: `src/agents/planner.py`

- Fetches Jira issue details
- Creates implementation plan
- Sets branch name from ticket ID

### 5.3 Implementer Agent

**File**: `src/agents/implementer.py`

- Clones repository
- Creates/checks out branch
- Implements code changes based on plan
- Uses LLM to generate code

### 5.4 Tester Agent

**File**: `src/agents/tester.py`

- Runs test suite (Jest)
- Analyzes failures
- Fixes code if needed
- Tracks iteration count

### 5.5 Reporter Agent

**File**: `src/agents/reporter.py`

- Commits and pushes changes
- Creates/updates pull request
- Transitions Jira to "In Review"
- Sends Discord notification

---

## Phase 6: Workflow Graph

### 6.1 Create Graph

**File**: `src/agents/graph.py`

```python
def create_dev_workflow(llm=None, checkpointer=None):
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("implementer", implementer_node)
    graph.add_node("tester", tester_node)
    graph.add_node("reporter", reporter_node)
    
    # Set entry point
    graph.set_entry_point("supervisor")
    
    # Add routing edges
    graph.add_conditional_edges("supervisor", route_decision, {...})
    
    # Add cycle-back edges
    for node in ["planner", "implementer", "tester", "reporter"]:
        graph.add_edge(node, "supervisor")
    
    return graph.compile(checkpointer=checkpointer)
```

---

## Phase 7: CLI Entry Point

### 7.1 Create CLI Script

**File**: `scripts/run_task.py`

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", required=True, help="Jira ticket ID")
    args = parser.parse_args()
    
    graph = create_dev_workflow()
    result = graph.invoke({"jira_ticket_id": args.ticket})
    
    print(f"Status: {result['status']}")
    print(f"PR URL: {result.get('pr_url', 'N/A')}")
```

---

## Phase 8: Docker Configuration

### 8.1 Update Docker Setup

**File**: `docker/api/Dockerfile`
- Python 3.11 base image
- Install uv for dependency management
- Copy source and install

**File**: `compose/docker-compose.yml`
- Single service (api)
- Environment variables
- Volume mounts for logs

---

## Phase 9: Testing

See `TESTING_STRATEGY.md` for detailed testing plan.

---

## File Creation Order

Execute in this order to ensure dependencies are available:

1. `pyproject.toml`, `pytest.ini`, `.env.example`
2. `src/__init__.py`, `src/config.py`, `src/logger.py`
3. `src/clients/__init__.py`, `src/clients/github_client.py`
4. `src/clients/jira_client.py`, `src/clients/discord_client.py`
5. `src/tools/__init__.py`, `src/tools/github.py`
6. `src/tools/jira.py`, `src/tools/discord.py`, `src/tools/filesystem.py`
7. `src/agents/__init__.py`, `src/agents/state.py`
8. `src/agents/supervisor.py`, `src/agents/planner.py`
9. `src/agents/implementer.py`, `src/agents/tester.py`
10. `src/agents/reporter.py`, `src/agents/graph.py`
11. `tests/conftest.py`, `tests/mocks/*`
12. `tests/unit/*`, `tests/integration/*`
13. `scripts/run_task.py`
14. `docker/*`, `compose/*`

---

## Validation Checkpoints

After each phase, verify:

1. **Phase 2**: Clients can be instantiated (with mocked env)
2. **Phase 3**: Tools can be invoked with mock clients
3. **Phase 4**: State can be created and converted
4. **Phase 5**: Agents can run with mock dependencies
5. **Phase 6**: Graph compiles and routes correctly
6. **Phase 7**: CLI runs with test input
7. **Phase 8**: Docker builds and starts
8. **Phase 9**: All tests pass

---

## Migration Notes

- Keep `mcps/` directory until migration is complete
- Keep `gemini-cli/` for reference (system prompt logic)
- Old README.md will be replaced with new documentation
- Environment variables remain the same (add OPENAI_API_KEY)
