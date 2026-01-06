"""Implementer agent for code implementation."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.agents.prompts.implementer import IMPLEMENTATION_PROMPT, COMPLETION_CHECK_PROMPT
from src.agents.parsers import parse_code_response, parse_completion_check
from src.clients.github_client import GitHubClient, get_github_client
from src.logger import get_logger
from src.tools.git import clone_repo, configure_git_user, branch_exists_on_remote, checkout_branch, get_commit_log
from src.tools.filesystem import run_command, write_file

logger = get_logger(__name__)


class ImplementerAgent:
    """Implements code changes based on the plan."""
    
    def __init__(self, llm: BaseChatModel = None, github_client: GitHubClient = None):
        self.llm = llm
        self.github_client = github_client
    
    def _get_github_client(self) -> GitHubClient:
        return self.github_client or get_github_client()
    
    def run(self, state: AgentState) -> AgentState:
        """Implement code changes based on the plan."""
        logger.info(f"Implementer: starting for {state.jira_ticket_id}")
        
        try:
            repo_path = state.repo_path or f"/tmp/project_{state.jira_ticket_id}"
            
            clone_result = self._clone_and_setup(repo_path, state.branch_name)
            if not clone_result["success"]:
                state.error = f"Repository setup failed: {clone_result.get('error')}"
                state.status = "failed"
                return state
            
            state.repo_path = repo_path
            state.branch_exists = clone_result.get("branch_exists", False)
            
            if state.branch_exists:
                state.existing_context = self._gather_existing_context(state)
                
                if self.llm and self._check_completion(state):
                    logger.info("Implementer: existing code satisfies requirements, skipping")
                    state.skip_implementation = True
                    state.status = "implementing"
                    state.confidence["implementation"] = 0.9
                    return state
            
            if self.llm:
                code_changes = self._generate_implementation(state)
            else:
                code_changes = self._placeholder_implementation()
            
            self._write_files(repo_path, code_changes)
            
            state.code_changes = code_changes
            state.status = "implementing"
            state.confidence["implementation"] = 0.7
            
            logger.info(f"Implementer: completed {len(code_changes)} file(s)")
            
        except Exception as e:
            logger.error(f"Implementer error: {e}")
            state.error = f"Implementer error: {str(e)}"
            state.status = "failed"
        
        return state
    
    def _clone_and_setup(self, repo_path: str, branch_name: str) -> dict:
        """Clone repository and set up branch."""
        result = clone_repo.invoke({"repo_path": repo_path})
        if not result["success"]:
            return result
        
        configure_git_user.invoke({"repo_path": repo_path})
        
        branch_exists = branch_exists_on_remote.invoke({
            "repo_path": repo_path,
            "branch_name": branch_name,
        })
        
        if branch_exists:
            logger.info(f"Implementer: branch '{branch_name}' exists on remote")
            checkout_branch.invoke({"repo_path": repo_path, "branch_name": branch_name, "create": False})
        else:
            logger.info(f"Implementer: creating new branch '{branch_name}'")
            checkout_branch.invoke({"repo_path": repo_path, "branch_name": branch_name, "create": True})
        
        run_command.invoke({"command": "npm install", "cwd": repo_path, "timeout": 180})
        
        return {"success": True, "repo_path": repo_path, "branch_exists": branch_exists}
    
    def _gather_existing_context(self, state: AgentState) -> dict:
        """Gather context from existing branch."""
        context = {"commits": "", "pr_comments": "", "review_comments": ""}
        
        try:
            context["commits"] = get_commit_log.invoke({"repo_path": state.repo_path, "branch_name": state.branch_name})
            
            github = self._get_github_client()
            prs = github.list_pull_requests(state="all")
            matching_pr = next(
                (pr for pr in prs if pr["head"]["ref"] == state.branch_name),
                None,
            )
            
            if matching_pr:
                pr_number = matching_pr["number"]
                comments = github.get_pr_comments(pr_number)
                review_comments = github.get_pr_review_comments(pr_number)
                
                context["pr_comments"] = "\n".join(
                    f"- {c['user']}: {c['body']}" for c in comments[:5]
                )
                context["review_comments"] = "\n".join(
                    f"- {c['user']} on {c['path']}: {c['body']}" for c in review_comments[:5]
                )
                logger.info(f"Implementer: found PR #{pr_number}")
        except Exception as e:
            logger.warning(f"Implementer: failed to gather context: {e}")
        
        return context
    
    def _check_completion(self, state: AgentState) -> bool:
        """Check if existing code already satisfies Jira requirements."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "")
        
        existing_code = self._read_existing_code(state.repo_path)
        
        prompt = COMPLETION_CHECK_PROMPT.format(
            ticket_key=state.jira_ticket_id,
            summary=summary,
            description=description[:1000] if description else "No description",
            existing_code=existing_code[:2000],
            commit_history=state.existing_context.get("commits", ""),
        )
        
        messages = [
            SystemMessage(content="You evaluate if code satisfies requirements."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        is_complete, reason = parse_completion_check(response.content)
        logger.info(f"Implementer: completion check: {is_complete} - {reason}")
        return is_complete
    
    def _read_existing_code(self, repo_path: str) -> str:
        """Read existing source files for context."""
        ls_result = run_command.invoke({
            "command": "find src -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' | head -20",
            "cwd": repo_path,
        })
        files = ls_result.get("stdout", "").strip().split("\n")[:5]
        
        existing_code = ""
        for f in files:
            if f:
                read_result = run_command.invoke({
                    "command": f"head -50 {f}",
                    "cwd": repo_path,
                })
                existing_code += f"\n--- {f} ---\n{read_result.get('stdout', '')[:500]}"
        
        return existing_code
    
    def _build_context_section(self, state: AgentState) -> str:
        """Build context section for implementation prompt."""
        sections = []
        
        jira_comments = state.jira_details.get("recent_comments", [])
        if jira_comments:
            comment_lines = "\n".join(
                f"- {c.get('author', 'Unknown')}: {c.get('body', '')[:200]}"
                for c in jira_comments[:3]
            )
            sections.append(f"\n## Jira Comments\n{comment_lines}")
        
        if state.fix_suggestions:
            sections.append(f"\n## Previous Test Failures\n{state.test_results.get('output', '')[-1000:]}")
            sections.append(f"\n## Fix Suggestions\n{state.fix_suggestions}")
        
        if state.existing_context:
            if state.existing_context.get("commits"):
                sections.append(f"\n## Prior Commits\n{state.existing_context['commits']}")
            if state.existing_context.get("pr_comments"):
                sections.append(f"\n## PR Comments\n{state.existing_context['pr_comments']}")
        
        return "\n".join(sections)
    
    def _generate_implementation(self, state: AgentState) -> list[dict]:
        """Generate code implementation using LLM."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Feature implementation")
        
        prompt = IMPLEMENTATION_PROMPT.format(
            ticket_key=state.jira_ticket_id,
            summary=summary,
            branch_name=state.branch_name,
            implementation_plan=state.implementation_plan,
            context_section=self._build_context_section(state),
        )
        
        messages = [
            SystemMessage(content="You are an expert React developer."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        changes = parse_code_response(response.content)
        
        return changes if changes else self._placeholder_implementation()
    
    def _placeholder_implementation(self) -> list[dict]:
        """Create placeholder implementation when no LLM is available."""
        return [{
            "file": "src/components/Feature.jsx",
            "content": """import React from 'react';
import PropTypes from 'prop-types';

const Feature = ({ title, description }) => (
  <div className="feature">
    <h2>{title}</h2>
    <p>{description}</p>
  </div>
);

Feature.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
};

Feature.defaultProps = { description: '' };

export default Feature;
""",
            "action": "create",
        }]
    
    def _write_files(self, repo_path: str, code_changes: list[dict]) -> dict:
        """Write code changes to files."""
        results = []
        for change in code_changes:
            file_path = f"{repo_path}/{change['file']}"
            result = write_file.invoke({
                "path": file_path,
                "content": change["content"],
            })
            results.append(result)
        
        return {"success": all(r.get("success") for r in results)}
