import codecs
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FileReader(ABC):
    @abstractmethod
    def read_file(self, filepath: str, max_chars: int) -> str:
        pass


class DefaultFileReader(FileReader):
    def read_file(self, filepath: str, max_chars: int) -> str:
        """
        Read file content with proper permission and error handling.
        """
        if not os.path.exists(filepath):
            return "No description available"

        # Atomic file access check for Windows
        try:
            with open(filepath, "r"):
                has_access = True
        except (PermissionError, OSError):
            return "No description available"

        if not has_access or not os.access(filepath, os.R_OK):
            return "No description available"

        try:
            # Try UTF-8 first
            with codecs.open(filepath, "r", encoding="utf-8") as file:
                content = file.read(max_chars)
                if not content:
                    return "File found empty"
                return content
        except UnicodeDecodeError:
            try:
                # Fall back to UTF-16
                with codecs.open(filepath, "r", encoding="utf-16") as file:
                    content = file.read(max_chars)
                    if not content:
                        return "File found empty"
                    return content
            except (PermissionError, OSError):
                return "No description available"
            except Exception:
                return "No description available"
        except (PermissionError, OSError):
            return "No description available"
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return "No description available"


class CommentSyntax(ABC):
    @abstractmethod
    def get_syntax(self, file_extension: str) -> Dict[str, Optional[Tuple[str, str]]]:
        pass


class DefaultCommentSyntax(CommentSyntax):
    syntax = {
        ".py": {"single": "#", "multi": ('"""', '"""')},
        ".js": {"single": "//", "multi": ("/*", "*/")},
        ".ts": {"single": "//", "multi": ("/*", "*/")},
        ".tsx": {"single": "//", "multi": ("/*", "*/")},
        ".html": {"single": None, "multi": ("<!--", "-->")},
        ".css": {"single": None, "multi": ("/*", "*/")},
        ".java": {"single": "//", "multi": ("/*", "*/")},
        ".c": {"single": "//", "multi": ("/*", "*/")},
        ".cpp": {"single": "//", "multi": ("/*", "*/")},
    }

    def get_syntax(self, file_extension: str) -> Dict[str, Optional[Tuple[str, str]]]:
        return self.syntax.get(file_extension, {})


class CommentParser:
    """
    A parser for extracting GynTree comments from various file types.

    This parser supports both single-line and multi-line comments across different
    programming languages. It looks for comments that start with 'GynTree:' (case-insensitive)
    and extracts the content following this marker.

    Key behaviors:
    - Only the first GynTree comment in a file is extracted.
    - For multi-line comments, all lines after the GynTree marker are included until the end of the comment.
    - The parser preserves the original formatting of the comment, including newlines and indentation.
    - Comments not starting with 'GynTree:' are ignored.
    - If no GynTree comment is found, 'No description available' is returned.
    - For unsupported file types, 'Unsupported file type' is returned.
    - For empty files, 'File found empty' is returned.

    The parser supports various file types including Python, JavaScript, C++, HTML, and others.
    """

    def __init__(self, file_reader: FileReader, comment_syntax: CommentSyntax):
        self.file_reader = file_reader
        self.comment_syntax = comment_syntax
        self.gyntree_pattern = re.compile(r"(?i)gyntree:", re.IGNORECASE)

    def get_file_purpose(self, filepath: str) -> str:
        """
        Get the purpose of a file from its GynTree comments.

        Args:
            filepath: Path to the file to parse. Must not be None.

        Returns:
            str: The file's purpose or an appropriate message.

        Raises:
            ValueError: If filepath is None.
        """
        if filepath is None:
            raise ValueError("Filepath cannot be None")

        if not filepath:
            return "No description available"

        file_extension = os.path.splitext(filepath)[1].lower()
        syntax = self.comment_syntax.get_syntax(file_extension)
        if not syntax:
            logger.debug(f"Unsupported file type: {file_extension}")
            return "Unsupported file type"

        content = self.file_reader.read_file(filepath, 5000)
        if content in ["No description available", "File found empty"]:
            return content

        lines = content.splitlines()
        single_comment_result = None
        multi_comment_result = None

        # First check single-line comments at the file level
        if syntax["single"]:
            single_comment_result = self._extract_single_line_comment(
                lines, syntax["single"], ignore_docstring=True
            )

        # Then check multi-line comments if no single-line comment was found
        if not single_comment_result and syntax["multi"]:
            multi_comment_result = self._extract_multi_line_comment(
                lines, syntax["multi"], file_extension
            )

        # Return the first found comment
        return (
            single_comment_result or multi_comment_result or "No description available"
        )

    def _extract_multi_line_comment(
        self, lines: List[str], delimiters: Tuple[str, str], file_extension: str
    ) -> Optional[str]:
        start_delim, end_delim = delimiters
        in_comment = False
        comment_lines = []
        gyntree_found = False

        for line in lines:
            stripped = line.strip()

            # Handle start of multi-line comment
            if not in_comment and start_delim in line:
                in_comment = True
                start_index = line.index(start_delim) + len(start_delim)
                line = line[start_index:]
                stripped = line.strip()

            # Process comment content
            if in_comment:
                if not gyntree_found:
                    # Look for GynTree marker in current line
                    match = self.gyntree_pattern.search(stripped)
                    if match:
                        gyntree_found = True
                        line = line[line.find("GynTree:") + 8 :]
                        comment_lines = []

                if gyntree_found:
                    if end_delim in line:
                        end_index = line.index(end_delim)
                        if end_index > 0:
                            comment_lines.append(line[:end_index])
                        break
                    comment_lines.append(line)

            # Handle end of multi-line comment
            if end_delim in line:
                in_comment = False

        if comment_lines:
            return self._clean_multi_line_comment(comment_lines, file_extension)
        return None

    def _extract_single_line_comment(
        self, lines: List[str], delimiter: str, ignore_docstring: bool = False
    ) -> Optional[str]:
        in_docstring = False
        docstring_count = 0

        for line in lines:
            stripped = line.strip()

            # Track docstring state if needed
            if ignore_docstring:
                if '"""' in line or "'''" in line:
                    docstring_count += line.count('"""') + line.count("'''")
                    in_docstring = docstring_count % 2 != 0
                if in_docstring:
                    continue

            # Process single-line comments
            if stripped.startswith(delimiter):
                if self.gyntree_pattern.search(stripped):
                    if "::" in stripped:  # Skip malformed comments
                        continue
                    content = stripped[stripped.find("GynTree:") + 8 :].strip()
                    if content:
                        return " ".join(word for word in content.split() if word)

        return None

    def _clean_multi_line_comment(
        self, comment_lines: List[str], file_extension: str
    ) -> str:
        if not comment_lines:
            return ""

        # Remove empty lines at start and end
        while comment_lines and not comment_lines[0].strip():
            comment_lines.pop(0)
        while comment_lines and not comment_lines[-1].strip():
            comment_lines.pop()

        if file_extension == ".py":
            return self._clean_python_docstring(comment_lines)

        # Clean and join lines
        cleaned_lines = []
        for line in comment_lines:
            cleaned = line.strip()
            if cleaned:
                # Remove leading asterisks and clean spaces
                cleaned = cleaned.lstrip("*").strip()
                if cleaned:
                    words = [word for word in cleaned.split() if word]
                    cleaned_lines.append(" ".join(words))

        return " ".join(cleaned_lines).strip()

    def _clean_python_docstring(self, comment_lines: List[str]) -> str:
        if len(comment_lines) == 1:
            return " ".join(word for word in comment_lines[0].split() if word)

        cleaned_lines = []
        for line in comment_lines:
            cleaned = line.strip()
            if cleaned:
                words = [word for word in cleaned.split() if word]
                cleaned_lines.append(" ".join(words))

        return " ".join(cleaned_lines).strip()
