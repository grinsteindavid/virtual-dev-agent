"""Reporter agent for creating PRs and notifications."""

from src.agents.state import AgentState
from src.clients.github_client import GitHubClient, get_github_client
from src.clients.jira_client import JiraClient, get_jira_client
from src.clients.discord_client import DiscordClient, get_discord_client
from src.tools.git import commit_and_push
from src.logger import get_logger

logger = get_logger(__name__)


class ReporterAgent:
    """Creates PRs, updates Jira, and sends notifications."""
    
    def __init__(
        self,
        github_client: GitHubClient = None,
        jira_client: JiraClient = None,
        discord_client: DiscordClient = None,
    ):
        self.github_client = github_client
        self.jira_client = jira_client
        self.discord_client = discord_client
    
    def _get_github_client(self) -> GitHubClient:
        return self.github_client or get_github_client()
    
    def _get_jira_client(self) -> JiraClient:
        return self.jira_client or get_jira_client()
    
    def _get_discord_client(self) -> DiscordClient:
        return self.discord_client or get_discord_client()
    
    def run(self, state: AgentState) -> AgentState:
        """Create PR, update Jira, and notify Discord."""
        logger.info(f"Reporter: starting for {state.jira_ticket_id}")
        
        try:
            self._commit_and_push(state)
            pr_result = self._create_or_update_pr(state)
            
            if pr_result:
                state.pr_url = pr_result.get("html_url", "")
                state.pr_number = pr_result.get("number", 0)
            
            self._update_jira(state)
            self._send_discord_notification(state)
            
            state.status = "done"
            logger.info(f"Reporter: completed - PR: {state.pr_url}")
            
        except Exception as e:
            logger.error(f"Reporter error: {e}")
            state.error = f"Reporter error: {str(e)}"
            state.status = "failed"
        
        return state
    
    def _commit_and_push(self, state: AgentState) -> dict:
        """Commit and push changes using git tool."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        commit_msg = f"feat({state.jira_ticket_id}): {summary}"
        
        result = commit_and_push.invoke({
            "repo_path": state.repo_path,
            "branch_name": state.branch_name,
            "commit_message": commit_msg,
            "force": True,
        })
        
        if not result["success"]:
            logger.warning(f"Commit/push issue: {result.get('message')}")
        
        return result
    
    def _create_or_update_pr(self, state: AgentState) -> dict | None:
        """Create new PR or update existing one."""
        github = self._get_github_client()
        
        existing_prs = github.list_pull_requests(state="open")
        existing_pr = next(
            (pr for pr in existing_prs if pr["head"]["ref"] == state.branch_name),
            None,
        )
        
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        
        if existing_pr:
            logger.info(f"PR already exists: #{existing_pr['number']}")
            self._add_pr_update_comment(github, existing_pr, state)
            return existing_pr
        
        return self._create_new_pr(github, state, summary)
    
    def _add_pr_update_comment(self, github: GitHubClient, pr: dict, state: AgentState) -> None:
        """Add update comment to existing PR."""
        test_info = state.test_results or {}
        comment = f"""## Update from Virtual Dev Agent

**Jira Ticket**: {state.jira_ticket_id}

### Test Results
- Passed: {test_info.get('passed', 0)}
- Failed: {test_info.get('failed', 0)}
- Iterations: {state.test_iterations}

### Changes
{len(state.code_changes)} file(s) modified.
"""
        github.create_pr_comment(pull_number=pr["number"], body=comment)
    
    def _create_new_pr(self, github: GitHubClient, state: AgentState, summary: str) -> dict | None:
        """Create a new pull request."""
        test_info = state.test_results or {}
        pr_body = f"""## {state.jira_ticket_id}: {summary}

### Implementation Details
{state.implementation_plan[:500] if state.implementation_plan else 'See Jira ticket for details.'}

### Test Results
- **Passed**: {test_info.get('passed', 0)}
- **Failed**: {test_info.get('failed', 0)}
- **Iterations**: {state.test_iterations}

### Files Changed
{chr(10).join(f"- `{c['file']}`" for c in state.code_changes[:10])}

---
*Created by Virtual Dev Agent*
"""
        try:
            pr = github.create_pull_request(
                title=f"feat({state.jira_ticket_id}): {summary}",
                head=state.branch_name,
                base="main",
                body=pr_body,
            )
            logger.info(f"Created PR #{pr['number']}")
            return pr
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def _update_jira(self, state: AgentState) -> None:
        """Update Jira ticket status and add comment."""
        jira = self._get_jira_client()
        
        try:
            jira.add_comment(state.jira_ticket_id, self._build_jira_comment(state))
        except Exception as e:
            logger.warning(f"Failed to add Jira comment: {e}")
        
        self._transition_to_review(jira, state.jira_ticket_id)
    
    def _transition_to_review(self, jira: JiraClient, ticket_id: str) -> None:
        """Transition Jira ticket to 'In Review' status."""
        try:
            transitions = jira.get_transitions(ticket_id)
            review_transition = next(
                (t for t in transitions if "review" in t["name"].lower()),
                None,
            )
            if review_transition:
                jira.transition_issue(ticket_id, review_transition["id"])
                logger.info(f"Transitioned Jira to: {review_transition['name']}")
        except Exception as e:
            logger.warning(f"Failed to transition Jira: {e}")
    
    def _build_jira_comment(self, state: AgentState) -> str:
        """Build detailed Jira comment."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        test_info = state.test_results or {}
        
        files_section = self._format_files(state.code_changes)
        test_summary = self._format_test_summary(test_info)
        
        return f"""*Task* ☑ {state.jira_ticket_id}: {summary} {{color:#00875a}}IN REVIEW{{color}}: completed.

*Key Implementation Details:*
{files_section}

*Pull Request:* {state.pr_url or 'Pending'}

*Jest Test Results:*
{test_summary}

*Workflow Steps:*
# Planning → Implementation → Testing ({state.test_iterations} iteration(s)) → PR Created

----
_Generated by Virtual Dev Agent_
"""
    
    def _format_files(self, code_changes: list[dict]) -> str:
        """Format file changes for Jira comment."""
        if not code_changes:
            return "* No files changed"
        
        lines = []
        for change in code_changes[:8]:
            file_path = change.get("file", "unknown")
            action = "Created" if change.get("action") == "create" else "Updated"
            lines.append(f"* {action} `{file_path}`")
        
        if len(code_changes) > 8:
            lines.append(f"* ... and {len(code_changes) - 8} more file(s)")
        
        return "\n".join(lines)
    
    def _format_test_summary(self, test_info: dict) -> str:
        """Format test summary."""
        passed = test_info.get("passed", 0)
        failed = test_info.get("failed", 0)
        return f"Tests: {passed} passed, {failed} failed"
    
    def _send_discord_notification(self, state: AgentState) -> None:
        """Send completion notification to Discord."""
        discord = self._get_discord_client()
        
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        test_info = state.test_results or {}
        
        files_list = "\n".join(f"• `{c.get('file', 'unknown')}`" for c in state.code_changes[:5])
        if len(state.code_changes) > 5:
            files_list += f"\n• ... and {len(state.code_changes) - 5} more"
        
        passed = test_info.get('passed', 0)
        failed = test_info.get('failed', 0)
        
        details = f"""**Task**: {state.jira_ticket_id} - {summary}
**Status**: ✅ Completed → In Review
**Pull Request**: {state.pr_url or 'Pending'}
**Test Results**: {passed} passed, {failed} failed
**Files Changed** ({len(state.code_changes)}):
{files_list}"""
        
        try:
            notification_type = "success" if state.pr_url and failed == 0 else "warning" if failed > 0 else "info"
            discord.send_notification(
                type=notification_type,
                message=f"✅ {state.jira_ticket_id}: {summary}",
                details=details,
            )
        except Exception as e:
            logger.warning(f"Failed to send Discord notification: {e}")
