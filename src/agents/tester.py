"""Tester agent for running tests and handling failures."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.agents.prompts.tester import FIX_PROMPT
from src.tools.filesystem import run_command
from src.logger import get_logger

logger = get_logger(__name__)


class TesterAgent:
    """Runs tests and handles failures."""
    
    def __init__(self, llm: BaseChatModel = None):
        self.llm = llm
    
    def run(self, state: AgentState) -> AgentState:
        """Run tests and attempt to fix failures."""
        logger.info(f"Tester: running tests for {state.jira_ticket_id}, iteration {state.test_iterations + 1}")
        
        try:
            test_result = self._run_tests(state.repo_path)
            
            state.test_iterations += 1
            state.test_results = test_result
            
            state.status = "testing"
            state.confidence["testing"] = self._calculate_confidence(
                test_result=test_result,
                iterations=state.test_iterations,
            )
            
            if test_result["success"]:
                logger.info(f"Tester: all tests passed (confidence: {state.confidence['testing']:.2f})")
            else:
                logger.warning(f"Tester: tests failed - {test_result.get('summary', 'unknown error')}")
                
                if self.llm and state.test_iterations < 3:
                    self._attempt_fix(state, test_result)
            
        except Exception as e:
            logger.error(f"Tester error: {e}")
            state.error = f"Tester error: {str(e)}"
            state.test_results = {"success": False, "error": str(e)}
        
        return state
    
    def _run_tests(self, repo_path: str) -> dict:
        """Run the test suite."""
        result = run_command.invoke({
            "command": "npm test -- --watchAll=false --coverage --passWithNoTests",
            "cwd": repo_path,
            "timeout": 300,
        })
        
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        output = stdout + stderr
        
        passed = 0
        failed = 0
        
        if "Tests:" in output:
            import re
            passed_match = re.search(r"(\d+) passed", output)
            failed_match = re.search(r"(\d+) failed", output)
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
        
        success = result["success"] and failed == 0
        
        return {
            "success": success,
            "passed": passed,
            "failed": failed,
            "output": output[-2000:],
            "summary": f"{passed} passed, {failed} failed",
        }
    
    def _attempt_fix(self, state: AgentState, test_result: dict) -> None:
        """Generate fix suggestions for failing tests and store in state."""
        logger.info("Tester: generating fix suggestions")
        
        code_changes_str = "\n".join([
            f"File: {c['file']}\n```\n{c['content'][:500]}...\n```"
            for c in state.code_changes[:3]
        ])
        
        prompt = FIX_PROMPT.format(
            test_output=test_result.get("output", "")[-1500:],
            failed_summary=test_result.get("summary", "Unknown failures"),
            code_changes=code_changes_str,
        )
        
        messages = [
            SystemMessage(content="You are an expert at debugging React/JavaScript tests."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        
        state.fix_suggestions = response.content[:3000]
        logger.info(f"Tester: stored fix suggestions ({len(state.fix_suggestions)} chars)")

    def _calculate_confidence(self, test_result: dict, iterations: int) -> float:
        """Calculate testing confidence based on test results and iterations."""
        if not test_result:
            return 0.3
        
        passed = test_result.get("passed", 0)
        failed = test_result.get("failed", 0)
        total = passed + failed
        
        if test_result.get("success"):
            score = 0.85
            if total > 0:
                score += 0.1
            if total >= 5:
                score += 0.05
        else:
            if total > 0:
                pass_rate = passed / total
                score = 0.3 + (pass_rate * 0.4)
            else:
                score = 0.3
        
        iteration_penalty = (iterations - 1) * 0.1
        score -= iteration_penalty
        
        return min(max(round(score, 2), 0.1), 1.0)
