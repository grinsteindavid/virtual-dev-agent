# File Structure

Complete list of files to create for the LangGraph conversion.

## Project Root

```
virtual-dev-agent/
├── .env.example              # Environment template
├── pyproject.toml            # Python dependencies (uv)
├── pytest.ini                # Test configuration
├── Makefile                  # Dev commands
├── README.md                 # Updated documentation (replace existing)
```

## Source Code (`src/`)

```
src/
├── __init__.py
├── config.py                 # Environment configuration
├── logger.py                 # Logging setup
│
├── clients/                  # API client wrappers
│   ├── __init__.py
│   ├── github_client.py      # GitHub REST API client
│   ├── jira_client.py        # Jira REST API client
│   └── discord_client.py     # Discord webhook client
│
├── tools/                    # LangChain tools
│   ├── __init__.py           # Export all tools
│   ├── github.py             # GitHub tools
│   ├── jira.py               # Jira tools
│   ├── discord.py            # Discord tools
│   └── filesystem.py         # File/command tools
│
├── agents/                   # LangGraph agents
│   ├── __init__.py
│   ├── state.py              # GraphState, AgentState
│   ├── graph.py              # Workflow graph
│   ├── supervisor.py         # Routing agent
│   ├── planner.py            # Planning agent
│   ├── implementer.py        # Code implementation agent
│   ├── tester.py             # Test execution agent
│   └── reporter.py           # PR/notification agent
│
└── api/                      # FastAPI (optional)
    ├── __init__.py
    ├── app.py                # App factory
    └── routes/
        ├── __init__.py
        ├── health.py         # Health endpoint
        └── tasks.py          # Task endpoints
```

## Tests (`tests/`)

```
tests/
├── __init__.py
├── conftest.py               # Shared fixtures
│
├── mocks/                    # Mock implementations
│   ├── __init__.py
│   ├── mock_llm.py           # FakeLLM class
│   ├── mock_github.py        # MockGitHubClient + data
│   ├── mock_jira.py          # MockJiraClient + data
│   └── mock_discord.py       # MockDiscordClient
│
├── unit/                     # Unit tests (no network)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_clients/
│   │   ├── __init__.py
│   │   ├── test_github_client.py
│   │   ├── test_jira_client.py
│   │   └── test_discord_client.py
│   ├── test_tools/
│   │   ├── __init__.py
│   │   ├── test_github_tools.py
│   │   ├── test_jira_tools.py
│   │   ├── test_discord_tools.py
│   │   └── test_filesystem_tools.py
│   └── test_agents/
│       ├── __init__.py
│       ├── test_supervisor.py
│       ├── test_planner.py
│       ├── test_implementer.py
│       ├── test_tester.py
│       ├── test_reporter.py
│       └── test_graph.py
│
└── integration/              # Integration tests (network)
    ├── __init__.py
    ├── test_api_health.py
    ├── test_api_tasks.py
    └── test_full_workflow.py
```

## Scripts (`scripts/`)

```
scripts/
├── run_task.py               # CLI entry point
└── run_agent.py              # Alternative CLI
```

## Docker (`docker/`, `compose/`)

```
docker/
└── api/
    ├── Dockerfile            # Production image
    └── Dockerfile.dev        # Development image

compose/
├── docker-compose.yml        # Base services
├── docker-compose.dev.yml    # Dev overrides
└── docker-compose.prod.yml   # Prod overrides
```

## Documentation (`docs/`)

```
docs/
├── ARCHITECTURE.md           # System architecture
├── IMPLEMENTATION_PLAN.md    # Implementation steps
├── TOOLS_MAPPING.md          # MCP to LangGraph mapping
├── TESTING_STRATEGY.md       # Testing approach
└── FILE_STRUCTURE.md         # This file
```

---

## File Count Summary

| Category | Count |
|----------|-------|
| Root files | 5 |
| src/ | 19 |
| tests/ | 22 |
| scripts/ | 2 |
| docker/ | 4 |
| docs/ | 5 |
| **Total** | **57** |

---

## Creation Order

### Phase 1: Foundation
1. `pyproject.toml`
2. `pytest.ini`
3. `.env.example`
4. `Makefile`
5. `src/__init__.py`
6. `src/config.py`
7. `src/logger.py`

### Phase 2: Clients
8. `src/clients/__init__.py`
9. `src/clients/github_client.py`
10. `src/clients/jira_client.py`
11. `src/clients/discord_client.py`

### Phase 3: Tools
12. `src/tools/__init__.py`
13. `src/tools/github.py`
14. `src/tools/jira.py`
15. `src/tools/discord.py`
16. `src/tools/filesystem.py`

### Phase 4: Agents
17. `src/agents/__init__.py`
18. `src/agents/state.py`
19. `src/agents/supervisor.py`
20. `src/agents/planner.py`
21. `src/agents/implementer.py`
22. `src/agents/tester.py`
23. `src/agents/reporter.py`
24. `src/agents/graph.py`

### Phase 5: Mocks
25. `tests/__init__.py`
26. `tests/mocks/__init__.py`
27. `tests/mocks/mock_llm.py`
28. `tests/mocks/mock_github.py`
29. `tests/mocks/mock_jira.py`
30. `tests/mocks/mock_discord.py`
31. `tests/conftest.py`

### Phase 6: Unit Tests
32-44. Unit test files

### Phase 7: Integration Tests
45-47. Integration test files

### Phase 8: API (Optional)
48-52. API files

### Phase 9: Scripts & Docker
53-57. Scripts and Docker files
