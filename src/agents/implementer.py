"""Implementer agent for code implementation."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.clients.github_client import GitHubClient, get_github_client
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


IMPLEMENTATION_PROMPT = """You are a React/JavaScript developer implementing a feature using TDD (Test-Driven Development).

Jira Ticket: {ticket_key}
Summary: {summary}
Branch: {branch_name}

Implementation Plan:
{implementation_plan}
{context_section}

**IMPORTANT: You MUST follow TDD - every component/function MUST have a corresponding test file.**

For each feature, provide files in this order:
1. **Test file first** (e.g., `src/components/__tests__/MyComponent.test.jsx`)
2. **Implementation file** (e.g., `src/components/MyComponent.jsx`)

Test requirements:
- Use Jest and React Testing Library
- Test rendering, props, user interactions
- Include at least 2-3 test cases per component
- Import from '@testing-library/react' and 'react-router-dom' as needed

For each file provide:
1. The file path (relative to project root)
2. The complete file content

Focus on:
- Writing tests BEFORE or WITH implementation
- Clean, readable code
- Proper imports
- PropTypes or TypeScript types where appropriate
- Following React best practices

Respond with the implementation details in a structured format."""

COMPLETION_CHECK_PROMPT = """You are reviewing whether existing code satisfies Jira requirements.

Jira Ticket: {ticket_key}
Summary: {summary}
Description: {description}

Existing Implementation:
{existing_code}

Commit History:
{commit_history}

Does the existing code fully implement the Jira ticket requirements?
Respond with JSON: {{"complete": true/false, "reason": "brief explanation"}}"""


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
                code_changes = self._placeholder_implementation(state)
            
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
        """Clone repository and set up branch, detecting if branch already exists."""
        from src.tools.filesystem import run_command
        
        owner = config.github.owner
        repo = config.github.repo
        clone_url = f"https://github.com/{owner}/{repo}.git"
        
        result = run_command.invoke({
            "command": f"rm -rf {repo_path} && git clone {clone_url} {repo_path}",
            "timeout": 120,
        })
        
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        
        run_command.invoke({
            "command": 'git config user.email "virtual-dev@agent.local"',
            "cwd": repo_path,
        })
        run_command.invoke({
            "command": 'git config user.name "Virtual Dev Agent"',
            "cwd": repo_path,
        })
        
        check_remote = run_command.invoke({
            "command": f"git ls-remote --heads origin {branch_name}",
            "cwd": repo_path,
        })
        branch_exists = bool(check_remote.get("stdout", "").strip())
        
        if branch_exists:
            logger.info(f"Implementer: branch '{branch_name}' exists on remote, checking out")
            run_command.invoke({
                "command": f"git fetch origin {branch_name} && git checkout {branch_name}",
                "cwd": repo_path,
            })
        else:
            logger.info(f"Implementer: creating new branch '{branch_name}'")
            run_command.invoke({
                "command": f"git checkout -b {branch_name}",
                "cwd": repo_path,
            })
        
        run_command.invoke({
            "command": "npm install",
            "cwd": repo_path,
            "timeout": 180,
        })
        
        return {"success": True, "repo_path": repo_path, "branch_exists": branch_exists}
    
    def _gather_existing_context(self, state: AgentState) -> dict:
        """Gather context from existing branch: commits, PR comments."""
        context = {"commits": "", "pr_comments": "", "review_comments": ""}
        
        try:
            from src.tools.filesystem import run_command
            
            log_result = run_command.invoke({
                "command": "git log --oneline -n 10",
                "cwd": state.repo_path,
            })
            context["commits"] = log_result.get("stdout", "")[:1000]
            
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
                
                logger.info(f"Implementer: found PR #{pr_number} with {len(comments)} comments")
        except Exception as e:
            logger.warning(f"Implementer: failed to gather context: {e}")
        
        return context
    
    def _check_completion(self, state: AgentState) -> bool:
        """Check if existing code already satisfies Jira requirements."""
        from src.tools.filesystem import run_command
        
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "")
        
        ls_result = run_command.invoke({
            "command": "find src -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' | head -20",
            "cwd": state.repo_path,
        })
        files = ls_result.get("stdout", "").strip().split("\n")[:5]
        
        existing_code = ""
        for f in files:
            if f:
                read_result = run_command.invoke({
                    "command": f"head -50 {f}",
                    "cwd": state.repo_path,
                })
                existing_code += f"\n--- {f} ---\n{read_result.get('stdout', '')[:500]}"
        
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
        content = response.content.lower()
        
        import json
        import re
        try:
            match = re.search(r'\{[^}]+\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                is_complete = data.get("complete", False)
                reason = data.get("reason", "")
                logger.info(f"Implementer: completion check: {is_complete} - {reason}")
                return is_complete
        except (json.JSONDecodeError, ValueError):
            pass
        
        return '"complete": true' in content or '"complete":true' in content
    
    def _build_context_section(self, state: AgentState) -> str:
        """Build context section for implementation prompt."""
        sections = []
        
        jira_comments = state.jira_details.get("recent_comments", [])
        if jira_comments:
            comment_lines = "\n".join(
                f"- {c.get('author', 'Unknown')}: {c.get('body', '')[:200]}"
                for c in jira_comments[:3]
            )
            sections.append(f"\n## Jira Comments (Additional Requirements)\n{comment_lines}")
        
        if state.fix_suggestions:
            sections.append(f"\n## Previous Test Failures\n{state.test_results.get('output', '')[-1000:]}")
            sections.append(f"\n## Fix Suggestions\n{state.fix_suggestions}")
        
        if state.existing_context:
            if state.existing_context.get("commits"):
                sections.append(f"\n## Prior Commits on Branch\n{state.existing_context['commits']}")
            if state.existing_context.get("pr_comments"):
                sections.append(f"\n## PR Comments\n{state.existing_context['pr_comments']}")
            if state.existing_context.get("review_comments"):
                sections.append(f"\n## Code Review Comments\n{state.existing_context['review_comments']}")
        
        return "\n".join(sections)
    
    def _generate_implementation(self, state: AgentState) -> list[dict]:
        """Generate code implementation using LLM."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Feature implementation")
        
        context_section = self._build_context_section(state)
        
        prompt = IMPLEMENTATION_PROMPT.format(
            ticket_key=state.jira_ticket_id,
            summary=summary,
            branch_name=state.branch_name,
            implementation_plan=state.implementation_plan,
            context_section=context_section,
        )
        
        messages = [
            SystemMessage(content="You are an expert React developer."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        
        return self._parse_code_response(response.content)
    
    def _parse_code_response(self, content: str) -> list[dict]:
        """Parse LLM response to extract file changes."""
        import re
        
        changes = []
        lines = content.split("\n")
        current_file = None
        current_content = []
        in_code_block = False
        
        for line in lines:
            if line.startswith("```") and not in_code_block:
                in_code_block = True
                continue
            elif line.startswith("```") and in_code_block:
                if current_file and current_content:
                    changes.append({
                        "file": current_file,
                        "content": "\n".join(current_content),
                        "action": "create",
                    })
                current_content = []
                in_code_block = False
                continue
            
            if in_code_block:
                current_content.append(line)
            else:
                path = self._extract_file_path(line)
                if path:
                    current_file = path
        
        return changes if changes else self._placeholder_implementation(AgentState())
    
    def _extract_file_path(self, line: str) -> str | None:
        """Extract clean file path from a line that may contain markdown."""
        import re
        
        extensions = (r'\.test\.jsx?', r'\.test\.tsx?', r'\.jsx?', r'\.tsx?', r'\.css', r'\.json', r'\.md')
        pattern = r'((?:src|public|components|pages|utils|hooks|styles|tests?|__tests__)[/\w\-\.]*(?:' + '|'.join(extensions) + r'))'
        
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return match.group(1)
        
        if "file:" in line.lower():
            path = line.split(":", 1)[-1].strip()
            path = re.sub(r'^[\s\d\.\#\*\`]+', '', path)
            path = path.strip('`* ')
            if path and '/' in path:
                return path
        
        return None
    
    def _placeholder_implementation(self, state: AgentState) -> list[dict]:
        """Create placeholder implementation when no LLM is available."""
        return [
            {
                "file": "src/components/Feature.jsx",
                "content": """import React from 'react';
import PropTypes from 'prop-types';

const Feature = ({ title, description }) => {
  return (
    <div className="feature">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
};

Feature.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
};

Feature.defaultProps = {
  description: '',
};

export default Feature;
""",
                "action": "create",
            }
        ]
    
    def _write_files(self, repo_path: str, code_changes: list[dict]) -> dict:
        """Write code changes to files."""
        from src.tools.filesystem import write_file
        
        results = []
        for change in code_changes:
            file_path = f"{repo_path}/{change['file']}"
            result = write_file.invoke({
                "path": file_path,
                "content": change["content"],
            })
            results.append(result)
        
        return {"success": all(r.get("success") for r in results), "files": results}
