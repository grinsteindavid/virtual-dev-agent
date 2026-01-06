"""Tests for Discord tools."""

import pytest
from unittest.mock import patch

from src.tools.discord import (
    send_discord_message,
    send_discord_embed,
    send_discord_notification,
)
from tests.mocks.mock_discord import MockDiscordClient


class TestDiscordTools:
    """Tests for Discord LangChain tools."""
    
    @patch("src.tools.discord.get_discord_client")
    def test_send_discord_message(self, mock_get_client):
        client = MockDiscordClient()
        mock_get_client.return_value = client
        
        result = send_discord_message.invoke({
            "content": "Test message",
            "username": "Bot",
        })
        
        assert result["success"] is True
        assert ("send_message", "Test message", "Bot") in client.calls
    
    @patch("src.tools.discord.get_discord_client")
    def test_send_discord_embed(self, mock_get_client):
        client = MockDiscordClient()
        mock_get_client.return_value = client
        
        result = send_discord_embed.invoke({
            "title": "Test Title",
            "description": "Test description",
            "color": 0x00FF00,
        })
        
        assert result["success"] is True
        embed_calls = [c for c in client.calls if c[0] == "send_embed"]
        assert len(embed_calls) == 1
        assert embed_calls[0][1] == "Test Title"
    
    @patch("src.tools.discord.get_discord_client")
    def test_send_discord_notification_success(self, mock_get_client):
        client = MockDiscordClient()
        mock_get_client.return_value = client
        
        result = send_discord_notification.invoke({
            "type": "success",
            "message": "Task completed",
            "details": "All tests passed",
        })
        
        assert result["success"] is True
        notif_calls = [c for c in client.calls if c[0] == "send_notification"]
        assert len(notif_calls) == 1
        assert notif_calls[0][1] == "success"
        assert notif_calls[0][2] == "Task completed"
    
    @patch("src.tools.discord.get_discord_client")
    def test_send_discord_notification_error(self, mock_get_client):
        client = MockDiscordClient()
        mock_get_client.return_value = client
        
        result = send_discord_notification.invoke({
            "type": "error",
            "message": "Build failed",
        })
        
        assert result["success"] is True
        notif_calls = [c for c in client.calls if c[0] == "send_notification"]
        assert notif_calls[0][1] == "error"
