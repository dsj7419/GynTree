import codecs
import gc
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import psutil
import pytest

from services.CommentParser import (
    CommentParser,
    DefaultCommentSyntax,
    DefaultFileReader,
)

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)


class MockFileReader(DefaultFileReader):
    """Mock file reader that simulates different file access scenarios"""

    def __init__(self, behavior: str = "normal"):
        self.behavior = behavior
        self.calls = []

    def read_file(self, filepath: str, max_chars: int) -> str:
        """Mock read_file implementation with controlled behaviors"""
        self.calls.append((filepath, max_chars))

        if self.behavior == "normal":
            return super().read_file(filepath, max_chars)
        elif self.behavior == "permission_denied":
            return "No description available"
        elif self.behavior == "not_found":
            return "No description available"
        elif self.behavior == "empty":
            return "File found empty"
        else:
            raise ValueError(f"Unknown behavior: {self.behavior}")


class CommentParserTestHelper:
    """Enhanced helper class for comment parser testing"""

    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None
        self._setup_readers()
        self.comment_syntax = DefaultCommentSyntax()
        self.parser = CommentParser(self.file_reader, self.comment_syntax)

    def _setup_readers(self):
        """Setup different file readers for various test scenarios"""
        self.file_reader = MockFileReader("normal")
        self.permission_denied_reader = MockFileReader("permission_denied")
        self.not_found_reader = MockFileReader("not_found")
        self.empty_reader = MockFileReader("empty")

    def set_reader_behavior(self, behavior: str):
        """Switch file reader behavior"""
        self.file_reader.behavior = behavior
        self.parser = CommentParser(self.file_reader, self.comment_syntax)

    def create_test_file(self, filename: str, content: str) -> Path:
        """Create a test file with given content"""
        file_path = self.tmpdir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def track_memory(self) -> None:
        """Start memory tracking"""
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        """Check memory usage after operation"""
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 10 * 1024 * 1024:  # 10MB threshold
                logger.warning(
                    f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB"
                )


@pytest.fixture
def helper(tmpdir):
    """Create test helper instance with cleanup"""
    helper = CommentParserTestHelper(Path(tmpdir))
    yield helper
    gc.collect()


@pytest.mark.timeout(30)
def test_single_line_comment(helper):
    """Test single line comment parsing"""
    helper.track_memory()

    file_path = helper.create_test_file("test_file.py", "# GynTree: Test file purpose.")

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Test file purpose."

    helper.check_memory_usage("single line comment")


@pytest.mark.timeout(30)
def test_multiline_comment_js(helper):
    """Test JavaScript multiline comment parsing"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "test_file.js",
        """/* 
         * GynTree: Multiline comment
         * in JavaScript file.
         */""",
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Multiline comment in JavaScript file."

    helper.check_memory_usage("JS multiline comment")


@pytest.mark.timeout(30)
def test_multiline_comment_python(helper):
    """Test Python docstring parsing"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "test_file.py",
        '''"""
        GynTree: File contains test class.
        Manages test operations.
        """''',
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert "File contains test class" in result
    assert "Manages test operations" in result

    helper.check_memory_usage("Python docstring")


@pytest.mark.timeout(30)
def test_html_comment(helper):
    """Test HTML comment parsing"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "test_file.html", "<!-- GynTree: HTML file comment -->"
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "HTML file comment"

    helper.check_memory_usage("HTML comment")


@pytest.mark.timeout(30)
def test_multiple_comments(helper):
    """Test handling of multiple comments"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "test_file.py",
        """# Non-GynTree comment
        # GynTree: First GynTree comment
        # GynTree: Second GynTree comment""",
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "First GynTree comment"

    helper.check_memory_usage("multiple comments")


@pytest.mark.timeout(30)
def test_nested_comments(helper):
    """Test nested comment handling"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "test_file.py",
        '''"""
        Outer docstring
        # GynTree: Nested single-line comment
        """
        # GynTree: Main comment''',
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Main comment"

    helper.check_memory_usage("nested comments")


@pytest.mark.timeout(30)
def test_large_file_handling(helper):
    """Test handling of large files"""
    helper.track_memory()

    # Create large file with comment at start
    content = "# GynTree: Large file test\n" + "x = 1\n" * 10000

    file_path = helper.create_test_file("large_file.py", content)

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Large file test"

    helper.check_memory_usage("large file")


@pytest.mark.timeout(30)
def test_comment_at_end(helper):
    """Test comment at end of file"""
    helper.track_memory()

    content = "x = 1\n" * 100 + "# GynTree: End comment"
    file_path = helper.create_test_file("end_comment.py", content)

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "End comment"

    helper.check_memory_usage("end comment")


@pytest.mark.timeout(30)
def test_unicode_handling(helper):
    """Test handling of unicode characters"""
    helper.track_memory()

    content = "# GynTree: Unicode test 文字 🚀"
    file_path = helper.create_test_file("unicode_test.py", content)

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Unicode test 文字 🚀"

    helper.check_memory_usage("unicode")


@pytest.mark.timeout(30)
def test_empty_file(helper):
    """Test empty file handling"""
    helper.track_memory()

    file_path = helper.create_test_file("empty.py", "")

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "File found empty"

    helper.check_memory_usage("empty file")


@pytest.mark.timeout(30)
def test_unsupported_file_type(helper):
    """Test unsupported file type handling"""
    helper.track_memory()

    file_path = helper.create_test_file("test.xyz", "GynTree: Test")

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Unsupported file type"

    helper.check_memory_usage("unsupported type")


@pytest.mark.timeout(30)
def test_malformed_comments(helper):
    """Test handling of malformed comments"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "malformed.py",
        """#GynTree without colon
        # GynTree:: double colon
        # GynTree: valid comment""",
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "valid comment"

    helper.check_memory_usage("malformed comments")


@pytest.mark.timeout(30)
def test_mixed_comment_styles(helper):
    """Test handling of mixed comment styles"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "mixed.py",
        '''# Single line
        """
        GynTree: Docstring comment
        """
        # GynTree: Single line comment''',
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Single line comment"  # Single line comments take precedence

    helper.check_memory_usage("mixed styles")


@pytest.mark.timeout(30)
def test_comment_indentation(helper):
    """Test handling of indented comments"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "indented.py",
        """    # GynTree: Indented comment
        def function():
            # GynTree: Nested comment
            pass""",
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Indented comment"

    helper.check_memory_usage("indentation")


@pytest.mark.timeout(30)
def test_file_encoding(helper):
    """Test handling of different file encodings"""
    helper.track_memory()

    # Create file with explicit UTF-8 encoding
    file_path = helper.tmpdir / "encoded.py"
    with codecs.open(str(file_path), "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n# GynTree: Encoded file comment")

    result = helper.parser.get_file_purpose(str(file_path))
    assert result == "Encoded file comment"

    helper.check_memory_usage("encoding")


@pytest.mark.timeout(30)
def test_comment_cleanup(helper):
    """Test comment cleanup and formatting"""
    helper.track_memory()

    file_path = helper.create_test_file(
        "cleanup.py",
        """# GynTree: Comment with    extra    spaces
        # and line continuation""",
    )

    result = helper.parser.get_file_purpose(str(file_path))
    assert "  " not in result  # No double spaces
    assert result == "Comment with extra spaces"

    helper.check_memory_usage("cleanup")


@pytest.mark.timeout(30)
def test_performance_large_codebase(helper):
    """Test parser performance with large codebase"""
    helper.track_memory()

    # Create multiple files with varying content
    for i in range(100):
        content = f"# Line 1\n# GynTree: File {i} purpose\n" + "x = 1\n" * 100
        helper.create_test_file(f"file_{i}.py", content)

    # Parse all files
    start_time = datetime.now()
    for i in range(100):
        helper.parser.get_file_purpose(str(helper.tmpdir / f"file_{i}.py"))
    duration = (datetime.now() - start_time).total_seconds()

    assert duration < 5.0  # Should complete within 5 seconds
    helper.check_memory_usage("large codebase")


@pytest.mark.timeout(30)
def test_error_recovery(helper):
    """Test comprehensive error recovery scenarios"""
    helper.track_memory()

    # Test case 1: Non-existent file
    helper.set_reader_behavior("not_found")
    result = helper.parser.get_file_purpose("nonexistent_file.py")
    assert result == "No description available"
    assert helper.file_reader.calls[-1][0] == "nonexistent_file.py"

    # Test case 2: Permission denied
    helper.set_reader_behavior("permission_denied")
    result = helper.parser.get_file_purpose("locked_file.py")
    assert result == "No description available"
    assert helper.file_reader.calls[-1][0] == "locked_file.py"

    # Test case 3: Empty file
    helper.set_reader_behavior("empty")
    result = helper.parser.get_file_purpose("empty_file.py")
    assert result == "File found empty"
    assert helper.file_reader.calls[-1][0] == "empty_file.py"

    # Test case 4: Normal operation verification
    helper.set_reader_behavior("normal")
    test_file = helper.create_test_file("test.py", "# GynTree: Test content")
    result = helper.parser.get_file_purpose(str(test_file))
    assert result == "Test content"
    assert helper.file_reader.calls[-1][0] == str(test_file)

    helper.check_memory_usage("error recovery")


@pytest.mark.timeout(30)
def test_error_recovery_edge_cases(helper):
    """Test edge cases in error recovery"""
    helper.track_memory()

    # Test with None filepath
    with pytest.raises(Exception):
        helper.parser.get_file_purpose(None)

    # Test with empty filepath
    result = helper.parser.get_file_purpose("")
    assert result == "No description available"

    # Test with invalid file extension
    result = helper.parser.get_file_purpose("test")
    assert result == "Unsupported file type"

    helper.check_memory_usage("error recovery edge cases")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
