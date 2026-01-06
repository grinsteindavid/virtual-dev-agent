"""Parsers for LLM responses."""

import re
from src.logger import get_logger

logger = get_logger(__name__)


def parse_code_response(content: str) -> list[dict]:
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
        else:
            path = extract_file_path(line)
            if path:
                current_file = path
    
    return changes


def extract_file_path(line: str) -> str | None:
    """Extract clean file path from a line that may contain markdown."""
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


def parse_completion_check(content: str) -> tuple[bool, str]:
    """Parse completion check response from LLM."""
    import json
    
    try:
        match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            is_complete = data.get("complete", False)
            reason = data.get("reason", "")
            return is_complete, reason
    except (json.JSONDecodeError, ValueError):
        pass
    
    is_complete = '"complete": true' in content.lower() or '"complete":true' in content.lower()
    return is_complete, ""
