"""Implementer agent for code implementation."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


IMPLEMENTATION_PROMPT = """You are a React/JavaScript developer implementing a feature based on the plan below.

Jira Ticket: {ticket_key}
Summary: {summary}
Branch: {branch_name}

Implementation Plan:
{implementation_plan}

Based on the plan, generate the code implementation. For each file you need to create or modify, provide:
1. The file path (relative to project root)
2. The complete file content

Focus on:
- Clean, readable code
- Proper imports
- PropTypes or TypeScript types where appropriate
- Following React best practices

Respond with the implementation details in a structured format."""


class ImplementerAgent:
    """Implements code changes based on the plan."""
    
    def __init__(self, llm: BaseChatModel = None):
        self.llm = llm
    
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
            
            if self.llm:
                code_changes = self._generate_implementation(state)
            else:
                code_changes = self._placeholder_implementation(state)
            
            write_result = self._write_files(repo_path, code_changes)
            
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
        
        branch_result = run_command.invoke({
            "command": f"git checkout -b {branch_name} || git checkout {branch_name}",
            "cwd": repo_path,
        })
        
        install_result = run_command.invoke({
            "command": "npm install",
            "cwd": repo_path,
            "timeout": 180,
        })
        
        return {"success": True, "repo_path": repo_path}
    
    def _generate_implementation(self, state: AgentState) -> list[dict]:
        """Generate code implementation using LLM."""
        fields = state.jira_details.get("fields", {})
        summary = fields.get("summary", "Feature implementation")
        
        prompt = IMPLEMENTATION_PROMPT.format(
            ticket_key=state.jira_ticket_id,
            summary=summary,
            branch_name=state.branch_name,
            implementation_plan=state.implementation_plan,
        )
        
        messages = [
            SystemMessage(content="You are an expert React developer."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        
        return self._parse_code_response(response.content)
    
    def _parse_code_response(self, content: str) -> list[dict]:
        """Parse LLM response to extract file changes."""
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
            elif "file:" in line.lower() or line.endswith(".js") or line.endswith(".jsx") or line.endswith(".ts") or line.endswith(".tsx"):
                path = line.replace("File:", "").replace("file:", "").strip()
                path = path.strip("`").strip("*").strip()
                if path:
                    current_file = path
        
        return changes if changes else self._placeholder_implementation(AgentState())
    
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
