# Virtual Developer Agent

A Docker Compose project that creates an automated virtual developer capable of handling tasks from Jira, implementing features in a React application, and creating pull requests in GitHub.

The agent currently works with a boilerplate React application (https://github.com/grinsteindavid/boilerplate-react-app) which it clones as a starting point.

## Overview
Virtual Developer Agent automates end-to-end delivery of Jira tasks into a GitHub repository with tests, PRs, and final reporting.
It runs non-interactively in Docker Compose and coordinates with MCP servers for GitHub, Jira, and Discord.
Key docs: `gemini-cli/GEMINI.md`, `docker-compose.yml`, `gemini-cli/settings.json`.

## Architecture
- __Developer service (`gemini-cli/`)__: Runs the Gemini CLI with system instructions from `/app/GEMINI.md` and a plan at `/app/plan.md`.
- __MCP servers (`mcps/`)__: HTTP JSON-RPC servers:
  - Discord: `mcps/discord/mcp-server.js` on port 3001
  - GitHub: `mcps/github/mcp-server.js` on port 3002
  - Jira: `mcps/jira/index.js` on port 3003
- __Transport__: Express + `StreamableHTTPServerTransport` at `/mcp` with `mcp-session-id` headers. Endpoints configured in `gemini-cli/settings.json`.
- __Data flow__: Jira ticket -> clone repo -> branch -> implement + tests -> push -> PR -> Jira transition -> Discord summary.

## Prerequisites
- __Docker & Docker Compose__
- __GitHub__: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`
- __Jira__: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `JIRA_PROJECT`
- __Discord__: `DISCORD_WEBHOOK_URL`
- __Gemini__: `GEMINI_API_KEY`

## Setup
1. __Create `.env` in repo root__:
  ```
  GEMINI_API_KEY=your_gemini_api_key
  GITHUB_TOKEN=your_github_token
  GITHUB_OWNER=your_github_owner
  GITHUB_REPO=boilerplate-react-app
  JIRA_URL=https://your-domain.atlassian.net
  JIRA_USERNAME=your_email@example.com
  JIRA_API_TOKEN=your_jira_api_token
  JIRA_PROJECT=YOURPROJ
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  ```
2. __Set the Jira ticket__ in `gemini-cli/plan.md`, e.g.:
  ```
  - Jira Ticket ID: PROJ-123
  ```
3. __Optional__: If you change MCP ports/URLs, update `gemini-cli/settings.json`.
4. __Run__:
  ```
  docker-compose up --build
  ```

## Configuration notes
- `gemini-cli/GEMINI.md` is mounted to `/app/GEMINI.md` and selected via `GEMINI_SYSTEM_MD` in `docker-compose.yml`.
- `gemini-cli/settings.json` is mounted to `/app/.gemini/settings.json`.
- The developer container runs non-interactively: `gemini -d -y -p "@/app/plan.md"`.
- Inside the developer container, the working project root is `/app/project_dir`. All commands use absolute paths (`git -C /app/project_dir`, `npm --prefix /app/project_dir`).

## How it works (end-to-end)
1. __Initial setup__: Clone target repo into `/app/project_dir` and validate remote (see `gemini-cli/GEMINI.md` “Repository Setup”).
2. __Branch management__: Create/checkout the branch named by the Jira ticket in `gemini-cli/plan.md`.
3. __Implementation__: Add tests first, implement minimal code to pass them.
4. __Testing__: Run Jest
5. __Verification__: Re-run tests, capture logs.
6. __Reporting & submission__:
  - Commit and push the task branch.
  - Create or update the GitHub Pull Request.
  - Transition Jira from “In Progress” to “In Review” using available transition IDs.
  - Send a single final summary to Discord.

## Services and endpoints
- Discord MCP: `http://localhost:3001/health`, `http://localhost:3001/mcp`
- GitHub MCP: `http://localhost:3002/health`, `http://localhost:3002/mcp`
- Jira MCP: `http://localhost:3003/health`, `http://localhost:3003/mcp`

## Observability & Logs

- Console logs (recommended):
  ```bash
  docker compose logs -f discord-mcp
  docker compose logs -f github-mcp
  docker compose logs -f jira-mcp
  ```

- File logs (inside containers):
  - Discord: `/app/discord-mcp.log`
  - GitHub: `/app/github-mcp.log`
  - Jira: `/app/jira-mcp.log`
  - Tail example:
    ```bash
    # Discord MCP
    docker ps --filter "name=discord-mcp" --format "{{.ID}}" | xargs -I {} \
      docker exec -it {} sh -c 'tail -n 200 -f /app/discord-mcp.log'
    ```
  - Note: File logs are ephemeral unless you persist them. Prefer `docker compose logs`,
    or modify the Winston file transport to write to a mounted directory if long-term
    retention is required.

- Health checks:
  ```bash
  curl -f http://localhost:3001/health
  curl -f http://localhost:3002/health
  curl -f http://localhost:3003/health
  ```

## Why use this project
- __Automation__: Hands-off implementation from ticket to PR.
- __Reproducibility__: Non-interactive, deterministic workflow in containers.
- __Quality gates__: Test-first, coverage goals, and verification steps.
- __Integrations__: First-class GitHub, Jira, Discord via MCP.
- __Extensible__: Add new MCP tools or services following the existing pattern.

## Troubleshooting

- Missing `package.json` after clone
  - Verify `GITHUB_OWNER/GITHUB_REPO` are correct and the React app lives at the repo root
- Jira issue not found or permission errors
  - Confirm `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, and ticket ID in `plan.md`
- No Discord message
  - Check `DISCORD_WEBHOOK_URL` and that the workflow reached the final reporting step
- Rebuild services
  - `docker-compose build --no-cache && docker-compose up`

## Example output

```bash
developer_1    | I have completed the task for Jira ticket DP-4.
developer_1    | 
developer_1    | Implementation Details:
developer_1    | - Created a new React component Greeting.jsx in src/components.
developer_1    | - Implemented the Greeting component to display a personalized greeting message.
developer_1    | - Added PropTypes for name to ensure type validation.
developer_1    | - Integrated logging using the logger utility for debugging purposes.
developer_1    | - Created a dedicated Jest test file Greeting.test.jsx in src/components.
developer_1    | - Wrote comprehensive tests covering happy path scenarios for the Greeting component.
developer_1    | 
developer_1    | Test Coverage:
developer_1    | - All 9 tests passed successfully.
developer_1    | - Test coverage for the new Greeting component is 100%.
developer_1    | 
developer_1    | Pull Request:
developer_1    | - A pull request has been created for the DP-4 branch: https://github.com/grinsteindavid/boilerplate-react-app/pull/new/DP-4
developer_1    | 
developer_1    | Next Steps:
developer_1    | - The Jira ticket DP-4 status should be updated to "In Review".
developer_1    | 
virtual-dev-agent_developer_1 exited with code 0
```
```bash
developer_1    | All steps of the development workflow have been completed. I have successfully:
developer_1    | 
developer_1    | 1.  **Initial Setup**: Cloned the repository, created/checked out the `DP-5` branch, and installed dependencies.
developer_1    | 2.  **Jira Task Intake and Analysis**: Read `plan.md`, fetched Jira task details for `DP-5`, and analyzed requirements. Noted that the task was already "In Review".
developer_1    | 3.  **Code Implementation**: Attempted to implement the Contact Us page, but encountered merge conflicts due to existing implementation on the remote branch. Resolved conflicts by accepting the remote's version.
developer_1    | 4.  **Testing and Refinement**: Ran Jest tests, which all passed.
developer_1    | 5.  **Verification**: Re-ran tests and captured logs.
developer_1    | 6.  **Reporting and Submission**: Committed resolved conflicts, pushed to the branch, commented on the existing Pull Request #4, updated the Jira task with a comment, and sent a final report to Discord.
developer_1    | 
developer_1    | The task is now fully processed according to the guidelines.
developer_1    | 
developer_1    | I am done with the task.
virtual-dev-agent_developer_1 exited with code 0
```

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

