"""Reporter agent for creating PRs and notifications."""

from langchain_core.language_models import BaseChatModel

from src.agents.state import AgentState
from src.clients.github_client import GitHubClient, get_github_client
from src.clients.jira_client import JiraClient, get_jira_client
from src.clients.discord_client import DiscordClient, get_discord_client
from src.config import config
from src.tools.filesystem import run_command
from src.logger import get_logger

logger = get_logger(__name__)


class ReporterAgent:
    """Creates PRs, updates Jira, and sends notifications."""
    
    def __init__(
        self,
        github_client: GitHubClient = None,
        jira_client: JiraClient = None,
        discord_client: DiscordClient = None,
        llm: BaseChatModel = None,
    ):
        self.github_client = github_client
        self.jira_client = jira_client
        self.discord_client = discord_client
        self.llm = llm
    
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
            commit_result = self._commit_and_push(state)
            if not commit_result["success"]:
                logger.warning(f"Commit/push issue: {commit_result.get('message')}")
            
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
        """Commit and push changes."""
        repo_path = state.repo_path
        branch = state.branch_name
        
        add_result = run_command.invoke({
            "command": "git add -A",
            "cwd": repo_path,
        })
        
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        commit_msg = f"feat({state.jira_ticket_id}): {summary}"
        
        commit_result = run_command.invoke({
            "command": f'git commit -m "{commit_msg}" --allow-empty',
            "cwd": repo_path,
        })
        
        token = config.github.token
        owner = config.github.owner
        repo = config.github.repo
        push_url = f"https://{token}@github.com/{owner}/{repo}.git"
        
        push_result = run_command.invoke({
            "command": f"git push {push_url} {branch} --force",
            "cwd": repo_path,
            "timeout": 60,
        })
        
        return {
            "success": push_result["success"],
            "message": push_result.get("stderr", "") or push_result.get("stdout", ""),
        }
    
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
            github.create_pr_comment(
                pull_number=existing_pr["number"],
                body=comment,
            )
            return existing_pr
        
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
        
        test_info = state.test_results or {}
        comment = f"""Virtual Dev Agent completed implementation.

*Pull Request*: {state.pr_url or 'Pending'}

*Test Results*:
- Passed: {test_info.get('passed', 0)}
- Failed: {test_info.get('failed', 0)}

*Files Changed*: {len(state.code_changes)}
"""
        
        try:
            jira.add_comment(state.jira_ticket_id, comment)
        except Exception as e:
            logger.warning(f"Failed to add Jira comment: {e}")
        
        try:
            transitions = jira.get_transitions(state.jira_ticket_id)
            review_transition = next(
                (t for t in transitions if "review" in t["name"].lower()),
                None,
            )
            if review_transition:
                jira.transition_issue(state.jira_ticket_id, review_transition["id"])
                logger.info(f"Transitioned Jira to: {review_transition['name']}")
        except Exception as e:
            logger.warning(f"Failed to transition Jira: {e}")
    
    def _send_discord_notification(self, state: AgentState) -> None:
        """Send completion notification to Discord."""
        discord = self._get_discord_client()
        
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        test_info = state.test_results or {}
        
        details = f"""**Jira**: {state.jira_ticket_id}
**PR**: {state.pr_url or 'Pending'}
**Tests**: {test_info.get('passed', 0)} passed, {test_info.get('failed', 0)} failed
**Files**: {len(state.code_changes)} changed"""
        
        try:
            discord.send_notification(
                type="success" if state.pr_url else "info",
                message=f"Completed: {summary}",
                details=details,
            )
        except Exception as e:
            logger.warning(f"Failed to send Discord notification: {e}")
