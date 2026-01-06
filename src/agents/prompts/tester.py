"""Prompt templates for the tester agent."""

FIX_PROMPT = """You are a React/JavaScript developer fixing test failures.

Test Output:
{test_output}

Failed Tests Summary:
{failed_summary}

Current code changes:
{code_changes}

Analyze the test failures and provide fixes. For each file that needs to be modified:
1. Identify the issue
2. Provide the corrected code

Focus on fixing the actual issues, not just making tests pass artificially."""
