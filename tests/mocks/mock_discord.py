"""Mock Discord client for unit tests."""


class MockDiscordClient:
    """Mock Discord client - no network calls."""
    
    def __init__(self):
        self.calls = []
    
    def send_message(self, content: str, username: str = None) -> dict:
        self.calls.append(("send_message", content, username))
        return {"success": True, "status": 204}
    
    def send_embed(
        self,
        title: str,
        description: str,
        color: int = None,
        url: str = None,
        username: str = None,
    ) -> dict:
        self.calls.append(("send_embed", title, description, color, url, username))
        return {"success": True, "status": 204}
    
    def send_notification(
        self,
        type: str,
        message: str,
        details: str = None,
    ) -> dict:
        self.calls.append(("send_notification", type, message, details))
        return {"success": True, "status": 204}
    
    def close(self):
        pass
