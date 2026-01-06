"""Tests for configuration module."""

import pytest
from unittest.mock import patch
import os


class TestConfig:
    """Tests for configuration loading."""
    
    def test_github_config_validation(self):
        from src.config import GitHubConfig
        
        valid = GitHubConfig(token="tok", owner="own", repo="rep")
        assert valid.is_valid is True
        
        invalid = GitHubConfig(token="", owner="own", repo="rep")
        assert invalid.is_valid is False
    
    def test_jira_config_validation(self):
        from src.config import JiraConfig
        
        valid = JiraConfig(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        assert valid.is_valid is True
        
        invalid = JiraConfig(url="", username="user", api_token="token", project="PROJ")
        assert invalid.is_valid is False
    
    def test_jira_config_host(self):
        from src.config import JiraConfig
        
        config = JiraConfig(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        assert config.host == "test.atlassian.net"
    
    def test_discord_config_validation(self):
        from src.config import DiscordConfig
        
        valid = DiscordConfig(webhook_url="https://discord.com/api/webhooks/...")
        assert valid.is_valid is True
        
        invalid = DiscordConfig(webhook_url="")
        assert invalid.is_valid is False
    
    def test_llm_config_validation(self):
        from src.config import LLMConfig
        
        openai = LLMConfig(openai_api_key="key", anthropic_api_key=None)
        assert openai.is_valid is True
        
        anthropic = LLMConfig(openai_api_key=None, anthropic_api_key="key")
        assert anthropic.is_valid is True
        
        neither = LLMConfig(openai_api_key=None, anthropic_api_key=None)
        assert neither.is_valid is False
    
    def test_redis_config_validation(self):
        from src.config import RedisConfig
        
        valid = RedisConfig(url="redis://localhost:6379/0")
        assert valid.is_valid is True
        
        invalid = RedisConfig(url="")
        assert invalid.is_valid is False
    
    def test_workflow_config_validation(self):
        from src.config import WorkflowConfig
        
        with_ticket = WorkflowConfig(ticket="DP-123")
        assert with_ticket.has_ticket is True
        
        without_ticket = WorkflowConfig(ticket=None)
        assert without_ticket.has_ticket is False
    
    def test_config_validate_returns_errors(self):
        from src.config import Config, GitHubConfig, JiraConfig, DiscordConfig, LLMConfig, RedisConfig, WorkflowConfig
        
        config = Config(
            github=GitHubConfig(token="", owner="", repo=""),
            jira=JiraConfig(url="", username="", api_token="", project=""),
            discord=DiscordConfig(webhook_url=""),
            llm=LLMConfig(openai_api_key=None, anthropic_api_key=None),
            redis=RedisConfig(url="redis://localhost:6379/0"),
            workflow=WorkflowConfig(ticket=None),
        )
        
        errors = config.validate()
        assert len(errors) == 4
        assert any("GitHub" in e for e in errors)
        assert any("Jira" in e for e in errors)
        assert any("Discord" in e for e in errors)
        assert any("LLM" in e for e in errors)
