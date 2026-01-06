"""Tests for DiscordClient."""

import pytest
from unittest.mock import patch, MagicMock

from src.clients.discord_client import DiscordClient, get_discord_client


class TestDiscordClient:
    """Tests for Discord webhook client."""
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_message_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_message("Test message")
        
        assert result["success"] is True
        assert result["status"] == 204
        mock_client.post.assert_called_once()
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_message_with_username(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_message("Test message", username="Bot")
        
        assert result["success"] is True
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["username"] == "Bot"
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_embed_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_embed(
            title="Test Title",
            description="Test description",
            color=0x00FF00,
        )
        
        assert result["success"] is True
        mock_client.post.assert_called_once()
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_embed_with_url(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_embed(
            title="Test",
            description="Desc",
            url="https://example.com",
        )
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_notification_info(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_notification(type="info", message="Info message")
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_notification_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_notification(type="success", message="Success!")
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_notification_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_notification(type="error", message="Error occurred")
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_notification_warning(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_notification(type="warning", message="Warning!")
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_send_notification_with_details(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        result = client.send_notification(
            type="info",
            message="Task completed",
            details="5 files changed",
        )
        
        assert result["success"] is True
    
    @patch("src.clients.discord_client.httpx.Client")
    def test_close_closes_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = DiscordClient(webhook_url="https://discord.com/api/webhooks/123/abc")
        client.close()
        
        mock_client.close.assert_called_once()


class TestGetDiscordClient:
    """Tests for singleton pattern."""
    
    def test_returns_client_instance(self):
        from src.clients import discord_client
        
        discord_client._discord_client = None
        
        with patch.object(DiscordClient, "__init__", return_value=None):
            client = get_discord_client()
            assert client is not None
