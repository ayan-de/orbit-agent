"""
File Operations tool for Orbit AI Agent.

Provides file reading, writing, and directory operations via NestJS Bridge.
"""

from typing import Optional, List, Any
import os
from pathlib import Path

from pydantic import BaseModel, Field, validator

from src.tools.base import OrbitTool, ToolCategory, ToolInput, ToolError
from src.bridge.client import bridge_client


class ListFilesInput(ToolInput):
    """Input schema for listing files."""
    path: str = Field(".", description="Directory path to list (default: current directory)")
    recursive: bool = Field(False, description="Recursively list subdirectories")
    include_hidden: bool = Field(False, description="Include hidden files (starting with '.')")
    pattern: Optional[str] = Field(None, description="File pattern to match (e.g., '*.py', '*.md')")


class ReadFileInput(ToolInput):
    """Input schema for reading a file."""
    path: str = Field(..., description="Path to the file to read")
    encoding: str = Field("utf-8", description="File encoding (default: utf-8)")
    max_lines: Optional[int] = Field(None, description="Maximum lines to read (optional)")


class WriteFileInput(ToolInput):
    """Input schema for writing a file."""
    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")
    encoding: str = Field("utf-8", description="File encoding (default: utf-8)")
    mode: str = Field("write", description="Write mode: 'write' or 'append'")
    create_dirs: bool = Field(False, description="Create parent directories if they don't exist")


class CreateDirectoryInput(ToolInput):
    """Input schema for creating a directory."""
    path: str = Field(..., description="Path to the directory to create")
    create_parents: bool = Field(True, description="Create parent directories if they don't exist")
    mode: Optional[str] = Field("0755", description="Directory mode (default: 0755)")


class DeletePathInput(ToolInput):
    """Input schema for deleting a file or directory."""
    path: str = Field(..., description="Path to the file or directory to delete")
    recursive: bool = Field(False, description="Recursively delete directories")
    force: bool = Field(False, description="Force delete without confirmation (for system files)")


class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    size: int
    is_directory: bool
    is_file: bool
    modified: Optional[str] = None
    permissions: Optional[str] = None


class FileOperationsTool(OrbitTool):
    """
    File operations tool.

    Provides file reading, writing, and directory management capabilities via NestJS Bridge.
    Useful for viewing code, configuration files, logs, and managing project files.
    """

    name: str = "file_ops"
    description: str = "Read, write, list, create, delete files and directories. Useful for viewing code, configuration files, logs, and managing project files."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 3  # File operations are moderately dangerous (out of 10)
    requires_confirmation: bool = True  # Require confirmation for write/delete operations
    args_schema: type[ToolInput] = Union[
        ListFilesInput,
        ReadFileInput,
        WriteFileInput,
        CreateDirectoryInput,
        DeletePathInput
    ]

    async def _arun(self, input_data: ToolInput, operation: str) -> str:
        """
        Execute file operation.

        Args:
            input_data: Validated tool input
            operation: Type of operation (list, read, write, mkdir, delete)

        Returns:
            Operation result or error message
        """
        try:
            if operation == "list":
                return await self._list_files(input_data)
            elif operation == "read":
                return await self._read_file(input_data)
            elif operation == "write":
                return await self._write_file(input_data)
            elif operation == "mkdir":
                return await self._create_directory(input_data)
            elif operation == "delete":
                return await self._delete_path(input_data)
            else:
                return f"Unknown operation: {operation}"

        except Exception as e:
            raise Exception(f"Error executing file operation: {str(e)}")

    async def _list_files(self, input: ListFilesInput) -> str:
        """List files in a directory."""
        response = await bridge_client.list_files(
            path=input.path,
            recursive=input.recursive,
            include_hidden=input.include_hidden,
            pattern=input.pattern
        )

        if response.exit_code != 0:
            raise Exception(f"Failed to list files: {response.stderr}")

        if not response.files:
            return f"No files found in '{input.path}'"

        # Format output
        output_lines = [f"Files in '{input.path}':"]

        for file_info in response.files:
            file_type = "DIR" if file_info.get("is_directory") else "FILE"
            size_str = self._format_size(file_info.get("size", 0))
            path_str = file_info.get("path", "")

            output_lines.append(f"  [{file_type}] {path_str} ({size_str})")
            if file_info.get("modified"):
                output_lines.append(f"  Modified: {file_info['modified']}")

        return "\n".join(output_lines)

    async def _read_file(self, input: ReadFileInput) -> str:
        """Read a file's contents."""
        response = await bridge_client.read_file(
            path=input.path,
            encoding=input.encoding,
            max_lines=input.max_lines
        )

        if response.exit_code != 0:
            raise Exception(f"Failed to read file: {response.stderr}")

        # Add path as context
        content = response.content or ""
        result = f"Contents of '{input.path}':\n\n{content}"

        # Truncate very large files
        if len(result) > 10000:
            result = result[:10000] + "\n\n[... Content truncated - file too large ...]"

        return result

    async def _write_file(self, input: WriteFileInput) -> str:
        """Write content to a file."""
        response = await bridge_client.write_file(
            path=input.path,
            content=input.content,
            encoding=input.encoding,
            mode=input.mode,
            create_dirs=input.create_dirs
        )

        if response.exit_code != 0:
            raise Exception(f"Failed to write file: {response.stderr}")

        return f"Successfully wrote {len(input.content)} characters to '{input.path}'"

    async def _create_directory(self, input: CreateDirectoryInput) -> str:
        """Create a directory."""
        response = await bridge_client.create_directory(
            path=input.path,
            create_parents=input.create_parents,
            mode=input.mode
        )

        if response.exit_code != 0:
            raise Exception(f"Failed to create directory: {response.stderr}")

        return f"Successfully created directory: '{input.path}'"

    async def _delete_path(self, input: DeletePathInput) -> str:
        """Delete a file or directory."""
        response = await bridge_client.delete_path(
            path=input.path,
            recursive=input.recursive,
            force=input.force
        )

        if response.exit_code != 0:
            raise Exception(f"Failed to delete path: {response.stderr}")

        return f"Successfully deleted: '{input.path}'"

    def _format_size(self, size: int) -> str:
        """Format file size for human readability."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size} {unit}"
            size /= 1024
        return f"{size} TB"

    def get_suggested_fix(self, error: Exception) -> Optional[str]:
        """
        Get suggested fix for common file operation errors.

        Args:
            error: The exception that occurred

        Returns:
            Suggested fix or None
        """
        error_str = str(error).lower()

        if "permission denied" in error_str or "access denied" in error_str:
            return "Check file permissions or try running with elevated privileges"
        elif "no such file" in error_str or "not found" in error_str or "does not exist" in error_str:
            return "Check if the file or directory exists"
        elif "is a directory" in error_str:
            return "Use 'list' operation instead for directories"
        elif "permission" in error_str:
            return "Check if you have write permissions to the target directory"
        elif "directory not empty" in error_str:
            return "Use recursive=True option to delete non-empty directories"

        return None
