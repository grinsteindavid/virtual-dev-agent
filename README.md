# Virtual Developer Agent

A Docker Compose project that creates an automated virtual developer capable of handling tasks from Jira, implementing features in a React application, and creating pull requests in GitHub.

The agent currently works with a boilerplate React application (https://github.com/grinsteindavid/boilerplate-react-app) which it clones as a starting point. The workflow includes:

1. Fetching tasks from Jira
2. Creating test files following TDD principles
3. Implementing the required features
4. Updating Jira task status to "In Review"
5. Adding a comprehensive summary comment in Jira
6. Creating a pull request in GitHub (if one doesn't exist)

Future enhancements will include a server with webhooks to fully automate the development task execution process.

## Prerequisites

- Docker and Docker Compose installed
- Credentials and tokens for the integrations you will use
  - GitHub: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` (and optionally `GITHUB_REPOSITORY_URL`)
  - Jira: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `JIRA_PROJECT`
  - Discord: `DISCORD_WEBHOOK_URL`
  - Gemini API: `GEMINI_API_KEY`

## Services

- `developer` (Gemini CLI runner)
- `discord-mcp` on http://localhost:3001
- `github-mcp` on http://localhost:3002
- `jira-mcp` on http://localhost:3003

## Configure

1) Create a `.env` file at the repo root with your values:

```env
GEMINI_API_KEY=your_gemini_api_key

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_OWNER=your_github_user_or_org
GITHUB_REPO=boilerplate-react-app

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=you@example.com
JIRA_API_TOKEN=atl-token
JIRA_PROJECT=DP

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

2) Define the task in `gemini-cli/plan.md`:

- Ensure it contains a canonical line like: `- Jira Ticket ID: DP-4` (example)
- Include a clear Task Description and Acceptance Criteria

3) (Optional) Adjust the model/flags by editing `developer` service command in `docker-compose.yml`.

## Quick Start

```bash
docker-compose up
```

- This starts all MCP servers and then the `developer` container, which reads:
  - `gemini-cli/GEMINI.md` for workflow rules
  - `gemini-cli/plan.md` for the current task
- To run detached: `docker-compose up -d`
- View logs: `docker-compose logs -f`
- Stop: `docker-compose down`

## What the Agent Does (high level)

The behavior follows `gemini-cli/GEMINI.md`:
1. Initial Setup
   - Clone the target GitHub repo and install dependencies
   - Ensure work happens on a branch named exactly as the Jira ticket (e.g., `DP-4`)
2. Jira Task Intake and Analysis
   - Parse `plan.md` for the Jira ticket ID
   - Query Jira via MCP to fetch the task details (read-only)
3. Test Creation
   - Create Jest tests first (TDD), covering happy paths, edge cases, and error handling
4. Code Implementation
   - Implement just enough code to make tests pass; follow component structure and PropTypes
5. Add Logging
   - Add `info`/`debug` logs around key operations
6. Testing and Refinement
   - Run Jest in CI mode; iterate until green
7. Verification
   - Confirm all tests pass; document assumptions in code comments/logs
8. Reporting and Submission
   - Commit, push, and create a Pull Request
   - Update Jira status from "In Progress" to "In Review" and post one final consolidated summary
   - Send the same final summary to Discord

Notes:
- Jira/Discord communications are gated until tests pass and a PR exists (final report only).
- The ticket ID in `plan.md` must match the actual Jira issue you have permission to view.

## Changing the Target Repository

- Set `GITHUB_OWNER`, `GITHUB_REPO`, and (optionally) `GITHUB_REPOSITORY_URL` in `.env`
- Ensure the repository contains a valid Node/React project with a `package.json` at its root

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

<img width="812" height="724" alt="image" src="https://github.com/user-attachments/assets/2150e3ed-06e4-4d97-8709-38b26fc26247" />

<img width="621" height="557" alt="image" src="https://github.com/user-attachments/assets/7acfb5ce-3bf1-4e38-9a69-9c91ecb58665" />

<img width="652" height="571" alt="image" src="https://github.com/user-attachments/assets/e536d671-8cab-4554-9d76-4f28fa48cee5" />

