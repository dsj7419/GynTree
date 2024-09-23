import re
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class FileReader(ABC):
    @abstractmethod
    def read_file(self, filepath: str, max_chars: int) -> str:
        pass

class DefaultFileReader(FileReader):
    def read_file(self, filepath: str, max_chars: int) -> str:
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read(max_chars)
        except FileNotFoundError:
            return ""
        except UnicodeDecodeError:
            return ""
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ""

class CommentSyntax(ABC):
    @abstractmethod
    def get_syntax(self, file_extension: str) -> Dict[str, Optional[Tuple[str, str]]]:
        pass

class DefaultCommentSyntax(CommentSyntax):
    syntax = {
        '.py': {'single': '#', 'multi': ('"""', '"""')},
        '.js': {'single': '//', 'multi': ('/*', '*/')},
        '.ts': {'single': '//', 'multi': ('/*', '*/')},
        '.tsx': {'single': '//', 'multi': ('/*', '*/')},
        '.html': {'single': None, 'multi': ('<!--', '-->')},
        '.css': {'single': None, 'multi': ('/*', '*/')},
        '.java': {'single': '//', 'multi': ('/*', '*/')},
        '.c': {'single': '//', 'multi': ('/*', '*/')},
        '.cpp': {'single': '//', 'multi': ('/*', '*/')}
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
        self.gyntree_pattern = re.compile(r'(?i)gyntree:', re.IGNORECASE)

    def get_file_purpose(self, filepath: str) -> str:
        file_extension = os.path.splitext(filepath)[1].lower()
        syntax = self.comment_syntax.get_syntax(file_extension)
        if not syntax:
            logger.debug(f"Unsupported file type: {file_extension}")
            return "Unsupported file type"

        content = self.file_reader.read_file(filepath, 5000)
        if not content:
            return "File found empty"

        description = self._extract_comment(content, syntax, file_extension)
        return description if description else "No description available"

    def _extract_comment(self, content: str, syntax: Dict[str, Optional[Tuple[str, str]]], file_extension: str) -> Optional[str]:
        lines = content.splitlines()
        
        if syntax['multi']:
            multi_comment = self._extract_multi_line_comment(lines, syntax['multi'], file_extension)
            if multi_comment:
                return multi_comment

        if syntax['single']:
            single_comment = self._extract_single_line_comment(lines, syntax['single'])
            if single_comment:
                return single_comment

        return None

    def _extract_multi_line_comment(self, lines: List[str], delimiters: Tuple[str, str], file_extension: str) -> Optional[str]:
        start_delim, end_delim = delimiters
        in_comment = False
        comment_lines = []
        gyntree_found = False

        for line in lines:
            if not in_comment and start_delim in line:
                in_comment = True
                start_index = line.index(start_delim) + len(start_delim)
                line = line[start_index:]
            
            if in_comment:
                if not gyntree_found:
                    match = self.gyntree_pattern.search(line)
                    if match:
                        gyntree_found = True
                        line = line[match.end():]
                        comment_lines = []
                
                if gyntree_found:
                    if end_delim in line:
                        end_index = line.index(end_delim)
                        comment_lines.append(line[:end_index])
                        break
                    comment_lines.append(line)
            
            if not in_comment and self.gyntree_pattern.search(line):
                return self._parse_comment_content(line)

        return self._clean_multi_line_comment(comment_lines, file_extension) if comment_lines else None

    def _extract_single_line_comment(self, lines: List[str], delimiter: str) -> Optional[str]:
        for line in lines:
            if line.strip().startswith(delimiter) and self.gyntree_pattern.search(line):
                return self._parse_comment_content(line)
        return None

    def _parse_comment_content(self, comment_content: str) -> str:
        match = self.gyntree_pattern.search(comment_content)
        if match:
            return comment_content[match.end():].strip()
        return comment_content.strip()

    def _clean_multi_line_comment(self, comment_lines: List[str], file_extension: str) -> str:
        while comment_lines and not comment_lines[0].strip():
            comment_lines.pop(0)
        while comment_lines and not comment_lines[-1].strip():
            comment_lines.pop()

        if not comment_lines:
            return ""

        if file_extension == '.py':
            return self._clean_python_docstring(comment_lines)

        min_indent = min(len(line) - len(line.lstrip()) for line in comment_lines if line.strip())
        cleaned_lines = [line[min_indent:] for line in comment_lines]
        cleaned_lines = [line.lstrip('* ').rstrip() for line in cleaned_lines]
        return '\n'.join(cleaned_lines).strip()

    def _clean_python_docstring(self, comment_lines: List[str]) -> str:
        if len(comment_lines) == 1:
            return comment_lines[0].strip()

        min_indent = min(len(line) - len(line.lstrip()) for line in comment_lines[1:] if line.strip())

        cleaned_lines = [comment_lines[0].strip()] + [
            line[min_indent:] if line.strip() else ''
            for line in comment_lines[1:]
        ]

        return '\n'.join(cleaned_lines).rstrip()