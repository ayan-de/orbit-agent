"""
File Operations tools for Orbit AI Agent.

Provides file reading, writing, and directory operations via NestJS Bridge.
Split into separate tools for easier LLM understanding and usage.
"""

from typing import Optional

from pydantic import Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput
from src.bridge.client import bridge_client


class ListFilesInput(ToolInput):
    """Input schema for listing files."""

    path: str = Field(
        ".", description="Directory path to list (default: current directory)"
    )


class ReadFileInput(ToolInput):
    """Input schema for reading a file."""

    path: str = Field(..., description="Path to the file to read")


class WriteFileInput(ToolInput):
    """Input schema for writing a file."""

    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")
    mode: str = Field("write", description="Write mode: 'write' or 'append'")
    create_dirs: bool = Field(
        True, description="Create parent directories if they don't exist"
    )


class CreateDirectoryInput(ToolInput):
    """Input schema for creating a directory."""

    path: str = Field(..., description="Path to the directory to create")
    create_parents: bool = Field(
        True, description="Create parent directories if they don't exist"
    )


class DeletePathInput(ToolInput):
    """Input schema for deleting a file or directory."""

    path: str = Field(..., description="Path to the file or directory to delete")
    recursive: bool = Field(False, description="Recursively delete directories")
    force: bool = Field(False, description="Force delete without confirmation")


def _format_size(size: int) -> str:
    """Format file size for human readability."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size} {unit}"
        size = int(size / 1024)
    return f"{size} TB"


class ListFilesTool(OrbitTool):
    """List files in a directory."""

    name: str = "list_files"
    description: str = "List files and directories in a given path. Shows file names, sizes, and types."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 1
    requires_confirmation: bool = False
    args_schema: type = ListFilesInput

    async def _arun(self, path: str = ".") -> str:
        try:
            response = await bridge_client.list_files(path=path)

            if response.exit_code != 0:
                raise Exception(f"Failed to list files: {response.stderr}")

            return response.stdout or f"No files found in '{path}'"

        except Exception as e:
            raise Exception(f"Error listing files: {str(e)}")


class ReadFileTool(OrbitTool):
    """Read contents of a file."""

    name: str = "read_file"
    description: str = "Read and return the contents of a file. Useful for viewing code, config files, logs."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 1
    requires_confirmation: bool = False
    args_schema: type = ReadFileInput

    async def _arun(self, path: str) -> str:
        try:
            response = await bridge_client.read_file(path=path)

            if response.exit_code != 0:
                raise Exception(f"Failed to read file: {response.stderr}")

            content = response.stdout or ""
            result = f"Contents of '{path}':\n\n{content}"

            if len(result) > 10000:
                result = (
                    result[:10000] + "\n\n[... Content truncated - file too large ...]"
                )

            return result

        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")


class WriteFileTool(OrbitTool):
    """Write content to a file."""

    name: str = "write_file"
    description: str = "Write content to a file. Creates the file if it doesn't exist. Can create parent directories."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 3
    requires_confirmation: bool = True
    args_schema: type = WriteFileInput

    async def _arun(
        self, path: str, content: str, mode: str = "write", create_dirs: bool = True
    ) -> str:
        try:
            response = await bridge_client.write_file(
                path=path, content=content, mode=mode, create_dirs=create_dirs
            )

            if response.exit_code != 0:
                raise Exception(f"Failed to write file: {response.stderr}")

            return f"Successfully wrote {len(content)} characters to '{path}'"

        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}")


class CreateDirectoryTool(OrbitTool):
    """Create a directory."""

    name: str = "create_directory"
    description: str = "Create a new directory. Can create parent directories automatically (like mkdir -p)."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 2
    requires_confirmation: bool = True
    args_schema: type = CreateDirectoryInput

    async def _arun(self, path: str, create_parents: bool = True) -> str:
        try:
            response = await bridge_client.create_directory(
                path=path, create_parents=create_parents
            )

            if response.exit_code != 0:
                raise Exception(f"Failed to create directory: {response.stderr}")

            return f"Successfully created directory: '{path}'"

        except Exception as e:
            raise Exception(f"Error creating directory: {str(e)}")


class DeletePathTool(OrbitTool):
    """Delete a file or directory."""

    name: str = "delete_path"
    description: str = (
        "Delete a file or directory. Use recursive=True for non-empty directories."
    )
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 4
    requires_confirmation: bool = True
    args_schema: type = DeletePathInput

    async def _arun(
        self, path: str, recursive: bool = False, force: bool = False
    ) -> str:
        try:
            response = await bridge_client.delete_path(
                path=path, recursive=recursive, force=force
            )

            if response.exit_code != 0:
                raise Exception(f"Failed to delete path: {response.stderr}")

            return f"Successfully deleted: '{path}'"

        except Exception as e:
            raise Exception(f"Error deleting path: {str(e)}")
