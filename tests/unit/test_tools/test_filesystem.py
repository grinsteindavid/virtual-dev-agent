"""Tests for filesystem tools."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.filesystem import (
    read_file,
    write_file,
    run_command,
    list_directory,
    file_exists,
)


class TestReadFile:
    """Tests for read_file tool."""
    
    def test_read_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            f.flush()
            temp_path = f.name
        
        try:
            result = read_file.invoke({"path": temp_path})
            assert result == "Hello, World!"
        finally:
            os.unlink(temp_path)
    
    def test_read_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_file.invoke({"path": "/nonexistent/path/file.txt"})
    
    def test_read_multiline_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3")
            f.flush()
            temp_path = f.name
        
        try:
            result = read_file.invoke({"path": temp_path})
            assert "Line 1" in result
            assert "Line 2" in result
            assert "Line 3" in result
        finally:
            os.unlink(temp_path)


class TestWriteFile:
    """Tests for write_file tool."""
    
    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            
            result = write_file.invoke({"path": file_path, "content": "Test content"})
            
            assert result["success"] is True
            assert Path(file_path).exists()
            assert Path(file_path).read_text() == "Test content"
    
    def test_write_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nested", "dir", "test.txt")
            
            result = write_file.invoke({"path": file_path, "content": "Nested content"})
            
            assert result["success"] is True
            assert Path(file_path).exists()
    
    def test_write_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            Path(file_path).write_text("Old content")
            
            result = write_file.invoke({"path": file_path, "content": "New content"})
            
            assert result["success"] is True
            assert Path(file_path).read_text() == "New content"
    
    def test_write_returns_bytes_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Test content 123"
            
            result = write_file.invoke({"path": file_path, "content": content})
            
            assert result["bytes_written"] == len(content)


class TestRunCommand:
    """Tests for run_command tool."""
    
    def test_run_successful_command(self):
        result = run_command.invoke({"command": "echo 'hello'"})
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "hello" in result["stdout"]
    
    def test_run_failing_command(self):
        result = run_command.invoke({"command": "exit 1"})
        
        assert result["success"] is False
        assert result["returncode"] == 1
    
    def test_run_command_with_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command.invoke({"command": "pwd", "cwd": tmpdir})
            
            assert result["success"] is True
            assert tmpdir in result["stdout"]
    
    def test_run_command_captures_stderr(self):
        result = run_command.invoke({"command": "echo 'error' >&2"})
        
        assert "error" in result["stderr"]
    
    def test_run_command_timeout(self):
        result = run_command.invoke({
            "command": "sleep 10",
            "timeout": 1,
        })
        
        assert result["success"] is False
        assert "timed out" in result["stderr"].lower()
    
    def test_run_command_with_pipe(self):
        result = run_command.invoke({"command": "echo 'hello world' | grep hello"})
        
        assert result["success"] is True
        assert "hello" in result["stdout"]


class TestListDirectory:
    """Tests for list_directory tool."""
    
    def test_list_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(os.path.join(tmpdir, "file1.txt")).write_text("content")
            Path(os.path.join(tmpdir, "file2.txt")).write_text("content")
            os.makedirs(os.path.join(tmpdir, "subdir"))
            
            result = list_directory.invoke({"path": tmpdir})
            
            assert len(result) == 3
            names = [item["name"] for item in result]
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert "subdir" in names
    
    def test_list_nonexistent_directory_raises(self):
        with pytest.raises(FileNotFoundError):
            list_directory.invoke({"path": "/nonexistent/directory"})
    
    def test_list_file_raises_not_a_directory(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(NotADirectoryError):
                list_directory.invoke({"path": temp_path})
        finally:
            os.unlink(temp_path)
    
    def test_list_returns_item_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(os.path.join(tmpdir, "file.txt")).write_text("content")
            os.makedirs(os.path.join(tmpdir, "folder"))
            
            result = list_directory.invoke({"path": tmpdir})
            
            file_item = next(i for i in result if i["name"] == "file.txt")
            dir_item = next(i for i in result if i["name"] == "folder")
            
            assert file_item["type"] == "file"
            assert dir_item["type"] == "directory"
    
    def test_list_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_directory.invoke({"path": tmpdir})
            
            assert result == []


class TestFileExists:
    """Tests for file_exists tool."""
    
    def test_existing_file_returns_true(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = file_exists.invoke({"path": temp_path})
            assert result is True
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file_returns_false(self):
        result = file_exists.invoke({"path": "/nonexistent/path/file.txt"})
        assert result is False
    
    def test_existing_directory_returns_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = file_exists.invoke({"path": tmpdir})
            assert result is True
