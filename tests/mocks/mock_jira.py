"""Mock Jira client for unit tests."""

MOCK_ISSUE = {
    "id": "10001",
    "key": "DP-123",
    "fields": {
        "summary": "Create greeting component",
        "description": "Implement a Greeting component that displays personalized messages with PropTypes validation.",
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Developer"},
        "priority": {"name": "Medium"},
        "created": "2024-01-01T00:00:00.000Z",
        "updated": "2024-01-02T00:00:00.000Z",
        "attachment": [],
        "comment": {"comments": []},
    },
}

MOCK_TRANSITIONS = [
    {"id": "21", "name": "In Review", "to": {"name": "In Review"}},
    {"id": "31", "name": "Done", "to": {"name": "Done"}},
]

MOCK_COMMENT = {
    "id": "10001",
    "body": "Test comment",
}


class MockJiraClient:
    """Mock Jira client - no network calls."""
    
    def __init__(self):
        self.calls = []
        self.current_status = "In Progress"
    
    def get_issue(self, issue_key: str) -> dict:
        self.calls.append(("get_issue", issue_key))
        issue = {**MOCK_ISSUE, "key": issue_key}
        issue["fields"] = {**MOCK_ISSUE["fields"], "status": {"name": self.current_status}}
        return issue
    
    def list_issues(self, status: str = "To Do", limit: int = 10) -> list[dict]:
        self.calls.append(("list_issues", status, limit))
        return [MOCK_ISSUE]
    
    def add_comment(self, issue_key: str, comment: str) -> dict:
        self.calls.append(("add_comment", issue_key, comment))
        return {**MOCK_COMMENT, "body": comment}
    
    def get_transitions(self, issue_key: str) -> list[dict]:
        self.calls.append(("get_transitions", issue_key))
        return MOCK_TRANSITIONS
    
    def transition_issue(self, issue_key: str, transition_id: str) -> dict:
        self.calls.append(("transition_issue", issue_key, transition_id))
        transition = next((t for t in MOCK_TRANSITIONS if t["id"] == transition_id), None)
        if transition:
            self.current_status = transition["to"]["name"]
        return {"success": True, "new_status": self.current_status}
    
    def download_attachments(
        self,
        issue_key: str,
        types: list[str] = None,
        dest_dir: str = "/tmp",
    ) -> list[str]:
        self.calls.append(("download_attachments", issue_key, types, dest_dir))
        return []
    
    def close(self):
        pass
