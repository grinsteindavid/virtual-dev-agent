# Virtual Developer Agent

A Docker Compose project that creates an automated virtual developer capable of handling tasks from Jira, reporting status to Discord, and creating pull requests in GitHub.

## Overview

This project implements a virtual developer agent that integrates with multiple platforms to automate the software development workflow. By connecting to Jira for task management, Discord for communication, and GitHub for code management, the agent can work autonomously on assigned tasks.

## Architecture

The project is built using Docker Compose with multiple containerized services:

- **MCP Services**: Message Control Program services that handle integration with external platforms
  - Discord MCP: Handles communication with Discord
  - GitHub MCP: Manages GitHub repository interactions and pull requests
  - Jira MCP: Processes tasks and tickets from Jira
- **Gemini CLI**: Command-line interface for the Gemini AI model that powers the virtual developer

## Components

### Discord MCP

The Discord MCP service enables the virtual developer to:
- Report task progress and status updates
- Receive commands and feedback
- Share development insights and blockers

### GitHub MCP

The GitHub MCP service allows the virtual developer to:
- Create branches for new features or bug fixes
- Commit code changes
- Open pull requests with appropriate descriptions
- Respond to code review comments

### Jira MCP

The Jira MCP service helps the virtual developer to:
- Fetch assigned tasks and tickets
- Update ticket status as work progresses
- Add comments and work logs
- Link commits and pull requests to tickets

### Gemini CLI

The Gemini CLI component:
- Provides AI capabilities to understand and implement tasks
- Generates code based on task requirements
- Makes decisions about development approaches
- Coordinates between the different MCPs

## Workflow

1. The virtual developer receives a task from Jira through the Jira MCP
2. It analyzes the task requirements using Gemini AI
3. It creates a branch and implements the solution following these steps:
   - Creates Jest test files based on requirements
   - Implements code with comprehensive logging
   - Runs tests until they pass
4. It commits changes and creates a pull request via GitHub MCP
5. It reports progress and completion to Discord via Discord MCP
6. It updates the Jira ticket status via Jira MCP

## Setup and Usage

### Prerequisites

- Docker and Docker Compose installed
- API credentials for Discord, GitHub, and Jira
- Gemini API access

### Configuration

1. Clone this repository
2. Create configuration files for each service (see Configuration section)
3. Build and start the services using Docker Compose

```bash
# Always rebuild the developer image when starting
docker-compose up -d --build developer
```

Note: The `--build` flag ensures that the developer Dockerfile image is always rebuilt when executing Docker Compose, ensuring the latest code changes are included.

### Configuration

Create the following configuration files:

- `discord-config.json`: Discord bot token and channel IDs
- `github-config.json`: GitHub access tokens and repository information
- `jira-config.json`: Jira API credentials and project details
- `gemini-config.json`: Gemini API key and model settings

## Development

### Project Structure

The project requires the following structure:

```
virtual-dev-agent/
├── docker-compose.yml
├── README.md
├── gemini-guidelines.md     # Guidelines for Gemini CLI
├── boilerplate/             # React project boilerplate
│   ├── src/
│   ├── package.json
│   └── ...
└── mcps/
    ├── discord/
    ├── github/
    ├── jira/
    └── ...
```

### Boilerplate React Project

The `boilerplate/` directory contains a React project template that is shared with the developer agent's Docker container. This provides:

- A consistent starting point for all development tasks
- Pre-configured Jest testing environment
- Standard project structure and dependencies
- Development tools and configurations

When the developer agent is executed with a plan (from a Jira story), it uses this boilerplate as the foundation for implementing the required features.

### Gemini CLI Guidelines

The `gemini-guidelines.md` file contains instructions for the Gemini CLI on how to approach development tasks. Key requirements include:

- Creating Jest test files for every task (Jira story)
- Implementing comprehensive logging throughout the code
- Following test-driven development practices
- Executing Jest tests and analyzing results until tests pass

These guidelines ensure the virtual developer produces consistent, testable, and well-documented code.

### Adding New MCPs

To add support for additional platforms:

1. Create a new Dockerfile in the appropriate directory
2. Implement the MCP interface
3. Add the service to the docker-compose.yml file
4. Update the main coordinator to recognize the new MCP

## License

[Specify your license here]

## Contributing

[Guidelines for contributing to the project]