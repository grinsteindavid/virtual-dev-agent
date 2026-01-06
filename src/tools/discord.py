"""Discord LangChain tools."""

from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.clients.discord_client import get_discord_client
from src.logger import get_logger

logger = get_logger(__name__)


class SendDiscordMessageInput(BaseModel):
    """Input for send_discord_message tool."""
    content: str = Field(description="Message content to send")
    username: str = Field(default=None, description="Username to display (optional)")


class SendDiscordEmbedInput(BaseModel):
    """Input for send_discord_embed tool."""
    title: str = Field(description="Embed title")
    description: str = Field(description="Embed description")
    color: int = Field(default=None, description="Embed color (decimal)")
    url: str = Field(default=None, description="Embed URL")
    username: str = Field(default=None, description="Username to display (optional)")


class SendDiscordNotificationInput(BaseModel):
    """Input for send_discord_notification tool."""
    type: Literal["info", "success", "warning", "error"] = Field(description="Notification type")
    message: str = Field(description="Notification message")
    details: str = Field(default=None, description="Additional details (optional)")


@tool(args_schema=SendDiscordMessageInput)
def send_discord_message(content: str, username: str = None) -> dict:
    """Send a plain text message to Discord via webhook.
    
    Use this tool for simple status updates or messages.
    """
    logger.info(f"Tool send_discord_message called: content_length={len(content)}")
    client = get_discord_client()
    return client.send_message(content, username=username)


@tool(args_schema=SendDiscordEmbedInput)
def send_discord_embed(
    title: str,
    description: str,
    color: int = None,
    url: str = None,
    username: str = None,
) -> dict:
    """Send an embed message to Discord via webhook.
    
    Use this tool for formatted messages with titles, descriptions, and links.
    """
    logger.info(f"Tool send_discord_embed called: title={title}")
    client = get_discord_client()
    return client.send_embed(title, description, color=color, url=url, username=username)


@tool(args_schema=SendDiscordNotificationInput)
def send_discord_notification(
    type: str,
    message: str,
    details: str = None,
) -> dict:
    """Send a formatted notification to Discord.
    
    Use this tool to send color-coded notifications (info, success, warning, error).
    """
    logger.info(f"Tool send_discord_notification called: type={type}")
    client = get_discord_client()
    return client.send_notification(type, message, details=details)


DISCORD_TOOLS = [
    send_discord_message,
    send_discord_embed,
    send_discord_notification,
]
