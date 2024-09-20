from abc import ABC, abstractmethod
import os
import re
from typing import Dict, Tuple, Optional
import logging

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
    def get_syntax(self, file_extension: str) -> Dict[str, Optional[str]]:
        pass

class DefaultCommentSyntax(CommentSyntax):
    SYNTAX = {
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

    def get_syntax(self, file_extension: str) -> Dict[str, Optional[str]]:
        return self.SYNTAX.get(file_extension, {})

class CommentParser:
    def __init__(self, file_reader: FileReader, comment_syntax: CommentSyntax):
        self.file_reader = file_reader
        self.comment_syntax = comment_syntax
        self.gyntree_pattern = re.compile(r'gyntree:(.*)', re.IGNORECASE | re.DOTALL)

    def get_file_purpose(self, filepath: str) -> str:
        file_extension = os.path.splitext(filepath)[1].lower()
        syntax = self.comment_syntax.get_syntax(file_extension)
        if not syntax:
            logger.debug(f"Unsupported file type: {file_extension}")
            return "Unsupported file type"

        content = self.file_reader.read_file(filepath, 5000)
        if not content:
            return "File not found or empty"

        description = self._extract_comment(content, syntax)
        return description if description else "No description available"

    def _extract_comment(self, content: str, syntax: dict) -> Optional[str]:
        # Check for multi-line comments first
        if syntax['multi']:
            start_delim, end_delim = map(re.escape, syntax['multi'])
            pattern = rf'{start_delim}(.*?){end_delim}'
            for match in re.finditer(pattern, content, re.DOTALL):
                description = self._parse_comment_content(match.group(1))
                if description:
                    return description

        # Then check for single-line comments
        if syntax['single']:
            for line in content.splitlines():
                stripped_line = line.strip()
                if stripped_line.startswith(syntax['single']):
                    description = self._parse_comment_content(stripped_line[len(syntax['single']):].strip())
                    if description:
                        return description

        return None

    def _parse_comment_content(self, comment_content: str) -> Optional[str]:
        match = self.gyntree_pattern.search(comment_content)
        return match.group(1).strip() if match else None