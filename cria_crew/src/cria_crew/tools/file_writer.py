import os
from pathlib import Path
from crewai.tools import BaseTool
from typing import Optional

class FileWriterTool(BaseTool):
    """Tool for writing output to files with support for automatic directory creation."""

    name: str = "FileWriterTool"
    description: str = "Writes content to a file. Creates directories in the path if they don't exist."

    def _run(self, file_path: str, content: str) -> str:
        """
        Writes the given content to the specified file, creating any necessary directories.

        Args:
            file_path (str): The path where the file should be written.
            content (str): The content to write to the file.

        Returns:
            str: A message indicating success or failure.
        """
        try:
            # Use pathlib for cross-platform path handling
            path = Path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return f"Successfully wrote content to {file_path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

    def _args_schema(self):
        """Define the arguments schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path where the file should be written"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }