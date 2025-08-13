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
