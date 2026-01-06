"""Environment configuration for Virtual Developer Agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class GitHubConfig:
    """GitHub API configuration."""
    token: str
    owner: str
    repo: str
    
    @property
    def is_valid(self) -> bool:
        return all([self.token, self.owner, self.repo])


@dataclass(frozen=True)
class JiraConfig:
    """Jira API configuration."""
    url: str
    username: str
    api_token: str
    project: str
    
    @property
    def is_valid(self) -> bool:
        return all([self.url, self.username, self.api_token, self.project])
    
    @property
    def host(self) -> str:
        """Get Jira host without protocol."""
        return self.url.replace("https://", "").replace("http://", "")


@dataclass(frozen=True)
class DiscordConfig:
    """Discord webhook configuration."""
    webhook_url: str
    
    @property
    def is_valid(self) -> bool:
        return bool(self.webhook_url)


@dataclass(frozen=True)
class LLMConfig:
    """LLM configuration."""
    openai_api_key: str | None
    anthropic_api_key: str | None
    model: str = "gpt-4o-mini"
    
    @property
    def is_valid(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key)


@dataclass(frozen=True)
class RedisConfig:
    """Redis configuration for state persistence."""
    url: str
    
    @property
    def is_valid(self) -> bool:
        return bool(self.url)


@dataclass(frozen=True)
class WorkflowConfig:
    """Workflow configuration."""
    ticket: str | None
    
    @property
    def has_ticket(self) -> bool:
        return bool(self.ticket)


@dataclass(frozen=True)
class Config:
    """Application configuration."""
    github: GitHubConfig
    jira: JiraConfig
    discord: DiscordConfig
    llm: LLMConfig
    redis: RedisConfig
    workflow: WorkflowConfig
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if not self.github.is_valid:
            errors.append("GitHub configuration incomplete (GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO)")
        if not self.jira.is_valid:
            errors.append("Jira configuration incomplete (JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, JIRA_PROJECT)")
        if not self.discord.is_valid:
            errors.append("Discord configuration incomplete (DISCORD_WEBHOOK_URL)")
        if not self.llm.is_valid:
            errors.append("LLM configuration incomplete (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        return errors


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        github=GitHubConfig(
            token=os.getenv("GITHUB_TOKEN", ""),
            owner=os.getenv("GITHUB_OWNER", ""),
            repo=os.getenv("GITHUB_REPO", ""),
        ),
        jira=JiraConfig(
            url=os.getenv("JIRA_URL", ""),
            username=os.getenv("JIRA_USERNAME", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            project=os.getenv("JIRA_PROJECT", ""),
        ),
        discord=DiscordConfig(
            webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""),
        ),
        llm=LLMConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        ),
        redis=RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ),
        workflow=WorkflowConfig(
            ticket=os.getenv("TICKET"),
        ),
    )


config = load_config()
