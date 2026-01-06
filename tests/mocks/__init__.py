"""Mock implementations for unit tests."""

from tests.mocks.mock_llm import FakeLLM
from tests.mocks.mock_github import MockGitHubClient, MOCK_REPO, MOCK_PR
from tests.mocks.mock_jira import MockJiraClient, MOCK_ISSUE, MOCK_TRANSITIONS
from tests.mocks.mock_discord import MockDiscordClient

__all__ = [
    "FakeLLM",
    "MockGitHubClient",
    "MOCK_REPO",
    "MOCK_PR",
    "MockJiraClient",
    "MOCK_ISSUE",
    "MOCK_TRANSITIONS",
    "MockDiscordClient",
]
