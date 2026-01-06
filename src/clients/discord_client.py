"""Discord webhook client."""

from datetime import datetime, timezone

import httpx
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


class DiscordClient:
    """Client for Discord webhooks."""
    
    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or config.discord.webhook_url
        self._client = httpx.Client(timeout=30.0)
    
    def _send(self, payload: dict) -> dict:
        """Send a payload to the Discord webhook."""
        response = self._client.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return {"success": True, "status": response.status_code}
    
    def send_message(self, content: str, username: str | None = None) -> dict:
        """Send a plain text message."""
        logger.info(f"send_message: content_length={len(content)} username={username}")
        payload = {"content": content}
        if username:
            payload["username"] = username
        result = self._send(payload)
        logger.info(f"send_message: success status={result['status']}")
        return result
    
    def send_embed(
        self,
        title: str,
        description: str,
        color: int | None = None,
        url: str | None = None,
        username: str | None = None,
    ) -> dict:
        """Send an embed message."""
        logger.info(f"send_embed: title={title} has_url={bool(url)}")
        embed = {
            "title": title,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if color:
            embed["color"] = color
        if url:
            embed["url"] = url
        
        payload = {"embeds": [embed]}
        if username:
            payload["username"] = username
        
        result = self._send(payload)
        logger.info(f"send_embed: success status={result['status']}")
        return result
    
    def send_notification(
        self,
        type: str,
        message: str,
        details: str | None = None,
    ) -> dict:
        """Send a formatted notification."""
        logger.info(f"send_notification: type={type} message_length={len(message)}")
        
        colors = {
            "info": 0x3498DB,
            "success": 0x2ECC71,
            "warning": 0xF39C12,
            "error": 0xE74C3C,
        }
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        
        embed = {
            "title": f"{icons.get(type, '📢')} {type.capitalize()} Notification",
            "description": message,
            "color": colors.get(type, 0x808080),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if details:
            embed["fields"] = [{"name": "Details", "value": details, "inline": False}]
        
        payload = {
            "embeds": [embed],
            "username": "Virtual Dev Agent",
        }
        
        result = self._send(payload)
        logger.info(f"send_notification: success type={type} status={result['status']}")
        return result
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()


_discord_client: DiscordClient | None = None


def get_discord_client() -> DiscordClient:
    """Get or create the Discord client singleton."""
    global _discord_client
    if _discord_client is None:
        _discord_client = DiscordClient()
    return _discord_client
