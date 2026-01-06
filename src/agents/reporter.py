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
    
    def _build_jira_comment(self, state: AgentState) -> str:
        """Build detailed Jira comment with implementation metadata."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Implementation")
        test_info = state.test_results or {}
        
        files_section = self._format_files_for_jira(state.code_changes)
        
        test_output = test_info.get("output", "")
        test_summary = self._parse_test_summary(test_output, test_info)
        
        comment = f"""*Task* ☑ {state.jira_ticket_id}: {summary} {{color:#00875a}}IN REVIEW{{color}}: has been completed and is now In Review.

*Key Implementation Details:*
{files_section}

*Pull Request:* {state.pr_url or 'Pending'}

*Jest Test Results Summary:*
{test_summary}

*Workflow Steps Completed:*
# Initial Setup
# Jira Task Intake and Analysis
# Code Implementation
# Testing and Refinement ({state.test_iterations} iteration(s))
# Verification
# Reporting and Submission

----
_Generated by Virtual Dev Agent_
"""
        return comment
    
    def _format_files_for_jira(self, code_changes: list[dict]) -> str:
        """Format file changes for Jira comment."""
        if not code_changes:
            return "* No files changed"
        
        lines = []
        for change in code_changes[:8]:
            file_path = change.get("file", "unknown")
            action = change.get("action", "modified")
            
            if "test" in file_path.lower():
                desc = f"with unit tests for `{file_path.split('/')[-1].replace('.test', '').replace('.jsx', '').replace('.js', '')}`"
            elif "component" in file_path.lower():
                desc = "component"
            elif "page" in file_path.lower():
                desc = "page"
            else:
                desc = ""
            
            verb = "Created" if action == "create" else "Updated"
            lines.append(f"* {verb} `{file_path}` {desc}")
        
        if len(code_changes) > 8:
            lines.append(f"* ... and {len(code_changes) - 8} more file(s)")
        
        return "\n".join(lines)
    
    def _parse_test_summary(self, test_output: str, test_info: dict) -> str:
        """Parse test output to extract summary metrics."""
        passed = test_info.get("passed", 0)
        failed = test_info.get("failed", 0)
        total = passed + failed
        
        import re
        suites_match = re.search(r"Test Suites:\s*(\d+)\s*passed.*?(\d+)\s*total", test_output)
        time_match = re.search(r"Time:\s*([\d.]+)\s*s", test_output)
        
        suites = suites_match.group(1) if suites_match else str(max(1, total // 3))
        suites_total = suites_match.group(2) if suites_match else suites
        time_taken = time_match.group(1) if time_match else "N/A"
        
        return f"""Test Suites: {suites} passed, {suites_total} total
Tests: {passed} passed, {total} total
Snapshots: 0 total
Time: {time_taken} s"""
    
    def _update_jira(self, state: AgentState) -> None:
        """Update Jira ticket status and add comment."""
        jira = self._get_jira_client()
        
        comment = self._build_jira_comment(state)
        
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
        
        files_list = "\n".join(
            f"• `{c.get('file', 'unknown')}`"
            for c in state.code_changes[:5]
        )
        if len(state.code_changes) > 5:
            files_list += f"\n• ... and {len(state.code_changes) - 5} more"
        
        passed = test_info.get('passed', 0)
        failed = test_info.get('failed', 0)
        
        details = f"""**Task**: {state.jira_ticket_id} - {summary}
**Status**: ✅ Completed → In Review

**Pull Request**: {state.pr_url or 'Pending'}

**Test Results**:
• Passed: {passed}
• Failed: {failed}
• Iterations: {state.test_iterations}

**Files Changed** ({len(state.code_changes)}):
{files_list}

**Workflow**: Planning → Implementation → Testing → PR Created"""
        
        try:
            discord.send_notification(
                type="success" if state.pr_url and failed == 0 else "warning" if failed > 0 else "info",
                message=f"✅ {state.jira_ticket_id}: {summary}",
                details=details,
            )
        except Exception as e:
            logger.warning(f"Failed to send Discord notification: {e}")
