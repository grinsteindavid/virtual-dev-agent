"""Jira REST API client."""

import base64
from pathlib import Path

import httpx
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


class JiraClient:
    """Client for Jira REST API."""
    
    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
        project: str | None = None,
    ):
        self.url = (url or config.jira.url).rstrip("/")
        self.username = username or config.jira.username
        self.api_token = api_token or config.jira.api_token
        self.project = project or config.jira.project
        
        auth_string = f"{self.username}:{self.api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        self._client = httpx.Client(
            base_url=f"{self.url}/rest/api/2",
            headers={
                "Authorization": f"Basic {auth_bytes}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict | list:
        """Make an HTTP request to Jira API."""
        response = self._client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return {"success": True}
        return response.json()
    
    def get_issue(self, issue_key: str) -> dict:
        """Get issue details by key."""
        logger.info(f"get_issue: issue_key={issue_key}")
        data = self._request("GET", f"/issue/{issue_key}")
        logger.info(f"get_issue: success key={data.get('key')} status={data.get('fields', {}).get('status', {}).get('name')}")
        return {
            "id": data["id"],
            "key": data["key"],
            "fields": {
                "summary": data["fields"].get("summary"),
                "description": data["fields"].get("description"),
                "status": data["fields"].get("status", {}),
                "assignee": data["fields"].get("assignee"),
                "priority": data["fields"].get("priority"),
                "created": data["fields"].get("created"),
                "updated": data["fields"].get("updated"),
                "attachment": data["fields"].get("attachment", []),
                "comment": data["fields"].get("comment", {}),
            },
        }
    
    def list_issues(self, status: str = "To Do", limit: int = 10) -> list[dict]:
        """List issues filtered by status."""
        logger.info(f"list_issues: status={status} limit={limit}")
        jql = f'project = {self.project} AND status = "{status}" ORDER BY created DESC'
        data = self._request("GET", "/search", params={"jql": jql, "maxResults": limit})
        issues = data.get("issues", [])
        logger.info(f"list_issues: success count={len(issues)}")
        return [
            {
                "key": issue["key"],
                "fields": {
                    "summary": issue["fields"].get("summary"),
                    "status": issue["fields"].get("status", {}),
                    "assignee": issue["fields"].get("assignee"),
                    "priority": issue["fields"].get("priority"),
                },
            }
            for issue in issues
        ]
    
    def add_comment(self, issue_key: str, comment: str) -> dict:
        """Add a comment to an issue."""
        logger.info(f"add_comment: issue_key={issue_key} comment_length={len(comment)}")
        data = self._request("POST", f"/issue/{issue_key}/comment", json={"body": comment})
        logger.info(f"add_comment: success id={data.get('id')}")
        return {"id": data.get("id"), "body": data.get("body")}
    
    def get_comments(self, issue_key: str, limit: int = 10) -> list[dict]:
        """Get comments for an issue, most recent first."""
        logger.info(f"get_comments: issue_key={issue_key} limit={limit}")
        data = self._request("GET", f"/issue/{issue_key}/comment")
        comments = data.get("comments", [])
        recent = comments[-limit:] if len(comments) > limit else comments
        recent.reverse()
        logger.info(f"get_comments: success count={len(recent)}")
        return [
            {
                "id": c.get("id"),
                "author": c.get("author", {}).get("displayName", "Unknown"),
                "body": c.get("body", "")[:500],
                "created": c.get("created"),
            }
            for c in recent
        ]
    
    def get_transitions(self, issue_key: str) -> list[dict]:
        """Get available transitions for an issue."""
        logger.info(f"get_transitions: issue_key={issue_key}")
        data = self._request("GET", f"/issue/{issue_key}/transitions")
        transitions = data.get("transitions", [])
        logger.info(f"get_transitions: success count={len(transitions)}")
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "to": {"name": t["to"]["name"]},
            }
            for t in transitions
        ]
    
    def transition_issue(self, issue_key: str, transition_id: str) -> dict:
        """Transition an issue to a new status."""
        logger.info(f"transition_issue: issue_key={issue_key} transition_id={transition_id}")
        self._request("POST", f"/issue/{issue_key}/transitions", json={"transition": {"id": transition_id}})
        issue = self.get_issue(issue_key)
        new_status = issue["fields"]["status"].get("name", "Unknown")
        logger.info(f"transition_issue: success new_status={new_status}")
        return {"success": True, "new_status": new_status}
    
    def download_attachments(
        self,
        issue_key: str,
        types: list[str] | None = None,
        dest_dir: str = "/tmp",
    ) -> list[str]:
        """Download attachments from an issue."""
        logger.info(f"download_attachments: issue_key={issue_key} types={types} dest_dir={dest_dir}")
        types = types or ["image", "pdf", "csv"]
        
        issue = self.get_issue(issue_key)
        attachments = issue["fields"].get("attachment", [])
        
        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
        pdf_exts = {".pdf"}
        csv_exts = {".csv"}
        
        def matches_type(filename: str, mime: str) -> bool:
            lower = filename.lower()
            if "all" in types:
                return True
            if "image" in types and (mime.startswith("image/") or any(lower.endswith(e) for e in image_exts)):
                return True
            if "pdf" in types and ("pdf" in mime or any(lower.endswith(e) for e in pdf_exts)):
                return True
            if "csv" in types and (mime == "text/csv" or any(lower.endswith(e) for e in csv_exts)):
                return True
            return False
        
        filtered = [
            a for a in attachments
            if matches_type(a.get("filename", ""), a.get("mimeType", ""))
        ]
        
        if not filtered:
            logger.info(f"download_attachments: no matching attachments")
            return []
        
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        auth_string = f"{self.username}:{self.api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        saved_paths = []
        for att in filtered:
            url = att.get("content")
            filename = att.get("filename", f"attachment-{att.get('id', 'unknown')}")
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
            final_name = f"{issue_key}-{safe_name}"
            file_path = dest_path / final_name
            
            logger.info(f"download_attachments: downloading {filename} -> {file_path}")
            response = httpx.get(
                url,
                headers={"Authorization": f"Basic {auth_bytes}"},
                timeout=60.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            file_path.write_bytes(response.content)
            saved_paths.append(str(file_path))
        
        logger.info(f"download_attachments: success count={len(saved_paths)}")
        return saved_paths
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()


_jira_client: JiraClient | None = None


def get_jira_client() -> JiraClient:
    """Get or create the Jira client singleton."""
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraClient()
    return _jira_client
