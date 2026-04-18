import codecs
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union

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
        if not os.path.exists(filepath) or not self._has_read_access(filepath):
            return "No description available"

        content = self._read_with_encoding(filepath, max_chars, "utf-8")
        if content is not None:
            return content

        content = self._read_with_encoding(filepath, max_chars, "utf-16")
        if content is not None:
            return content

        return "No description available"

    def _has_read_access(self, filepath: str) -> bool:
        """Check if the file exists and is readable."""
        try:
            with open(filepath, "r"):
                return os.access(filepath, os.R_OK)
        except (PermissionError, OSError):
            return False

    def _read_with_encoding(
        self, filepath: str, max_chars: int, encoding: str
    ) -> Optional[str]:
        """Attempt to read the file with the given encoding."""
        try:
            with codecs.open(filepath, "r", encoding=encoding) as file:
                content = file.read(max_chars)
                return content if content else "File found empty"
        except UnicodeDecodeError:
            return None
        except (PermissionError, OSError):
            return "No description available"
        except Exception as e:
            logger.error(f"Error reading file {filepath} with {encoding}: {e}")
            return "No description available"


class CommentSyntax(ABC):
    @abstractmethod
    def get_syntax(
        self, file_extension: str
    ) -> Dict[str, Optional[Union[str, Tuple[str, str]]]]:
        pass


class DefaultCommentSyntax(CommentSyntax):
    syntax: Dict[str, Dict[str, Optional[Union[str, Tuple[str, str]]]]] = {
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

    def get_syntax(
        self, file_extension: str
    ) -> Dict[str, Optional[Union[str, Tuple[str, str]]]]:
        return self.syntax.get(file_extension, {"single": None, "multi": None})


class CommentParser:
    def __init__(self, file_reader: FileReader, comment_syntax: CommentSyntax):
        self.file_reader = file_reader
        self.comment_syntax = comment_syntax
        self.gyntree_pattern = re.compile(r"(?i)gyntree:", re.IGNORECASE)

    def get_file_purpose(self, filepath: str) -> str:
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

        single_line_syntax = syntax.get("single")
        multi_line_syntax = syntax.get("multi")

        if single_line_syntax:
            if isinstance(single_line_syntax, str):
                single_comment_result = self._extract_single_line_comment(
                    lines, single_line_syntax, ignore_docstring=True
                )

        if not single_comment_result and multi_line_syntax:
            if isinstance(multi_line_syntax, tuple):
                multi_comment_result = self._extract_multi_line_comment(
                    lines, multi_line_syntax, file_extension
                )

        return (
            single_comment_result or multi_comment_result or "No description available"
        )

    def _extract_multi_line_comment(
        self, lines: List[str], delimiters: Tuple[str, str], file_extension: str
    ) -> Optional[str]:
        start_delim, end_delim = delimiters
        in_comment = False
        comment_lines: List[str] = []
        gyntree_found = False

        for line in lines:
            stripped = line.strip()

            if not in_comment and start_delim in line:
                in_comment = True
                start_index = line.index(start_delim) + len(start_delim)
                line = line[start_index:]
                stripped = line.strip()

            if in_comment:
                if not gyntree_found:
                    match = self.gyntree_pattern.search(stripped)
                    if match:
                        gyntree_found = True
                        line = line[line.find("GynTree:") + 8 :].strip()
                        comment_lines = []

                if gyntree_found:
                    if end_delim in line:
                        end_index = line.index(end_delim)
                        if end_index > 0:
                            comment_lines.append(line[:end_index])
                        break
                    comment_lines.append(line)

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

            if ignore_docstring:
                if '"""' in line or "'''" in line:
                    docstring_count += line.count('"""') + line.count("'''")
                    in_docstring = docstring_count % 2 != 0
                if in_docstring:
                    continue

            if stripped.startswith(delimiter):
                if self.gyntree_pattern.search(stripped):
                    if "::" in stripped:
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

        while comment_lines and not comment_lines[0].strip():
            comment_lines.pop(0)
        while comment_lines and not comment_lines[-1].strip():
            comment_lines.pop()

        if file_extension == ".py":
            return self._clean_python_docstring(comment_lines)

        cleaned_lines = []
        for line in comment_lines:
            cleaned = line.strip()
            if cleaned:
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
