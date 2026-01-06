"""Filesystem and command LangChain tools."""

import subprocess
from pathlib import Path

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.logger import get_logger

logger = get_logger(__name__)


class ReadFileInput(BaseModel):
    """Input for read_file tool."""
    path: str = Field(description="Path to file")


class WriteFileInput(BaseModel):
    """Input for write_file tool."""
    path: str = Field(description="Path to file")
    content: str = Field(description="Content to write")


class RunCommandInput(BaseModel):
    """Input for run_command tool."""
    command: str = Field(description="Command to run")
    cwd: str = Field(default=None, description="Working directory (optional)")
    timeout: int = Field(default=300, description="Timeout in seconds")


class ListDirectoryInput(BaseModel):
    """Input for list_directory tool."""
    path: str = Field(description="Directory path")


class FileExistsInput(BaseModel):
    """Input for file_exists tool."""
    path: str = Field(description="Path to check")


@tool(args_schema=ReadFileInput)
def read_file(path: str) -> str:
    """Read contents of a file.
    
    Use this tool to read source code, configuration files, or any text file.
    """
    logger.info(f"Tool read_file called: path={path}")
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = file_path.read_text()
    logger.info(f"Tool read_file success: {len(content)} characters")
    return content


@tool(args_schema=WriteFileInput)
def write_file(path: str, content: str) -> dict:
    """Write content to a file.
    
    Use this tool to create or update source code files.
    Creates parent directories if they don't exist.
    """
    logger.info(f"Tool write_file called: path={path}, content_length={len(content)}")
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    logger.info(f"Tool write_file success: {path}")
    return {"success": True, "path": str(file_path.absolute()), "bytes_written": len(content)}


@tool(args_schema=RunCommandInput)
def run_command(command: str, cwd: str = None, timeout: int = 300) -> dict:
    """Run a shell command.
    
    Use this tool to execute git commands, npm/yarn, test runners, etc.
    Returns stdout, stderr, and return code.
    """
    logger.info(f"Tool run_command called: command={command[:100]}, cwd={cwd}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logger.info(f"Tool run_command completed: returncode={result.returncode}")
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Tool run_command timeout: {timeout}s")
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }
    except Exception as e:
        logger.error(f"Tool run_command error: {e}")
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


@tool(args_schema=ListDirectoryInput)
def list_directory(path: str) -> list[dict]:
    """List contents of a directory.
    
    Use this tool to explore project structure and find files.
    """
    logger.info(f"Tool list_directory called: path={path}")
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    
    items = []
    for item in sorted(dir_path.iterdir()):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "path": str(item.absolute()),
        })
    logger.info(f"Tool list_directory success: {len(items)} items")
    return items


@tool(args_schema=FileExistsInput)
def file_exists(path: str) -> bool:
    """Check if a file or directory exists.
    
    Use this tool to verify paths before reading or writing.
    """
    logger.info(f"Tool file_exists called: path={path}")
    exists = Path(path).exists()
    logger.info(f"Tool file_exists result: {exists}")
    return exists


FILESYSTEM_TOOLS = [
    read_file,
    write_file,
    run_command,
    list_directory,
    file_exists,
]
