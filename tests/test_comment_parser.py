"""
GynTree: This file contains unit tests for the CommentParser class, ensuring
accurate extraction of file purpose comments from various file types.
"""

import pytest
from services.CommentParser import CommentParser

def test_single_line_comment(tmpdir):
    file_path = tmpdir.join("test_file.py")
    file_path.write("# GynTree: This is a test file.")
    assert CommentParser.get_file_purpose(str(file_path)) == "This is a test file."

def test_multiline_comment(tmpdir):
    file_path = tmpdir.join("test_file.js")
    file_path.write("/* GynTree: Multiline comment for test file. */")
    assert CommentParser.get_file_purpose(str(file_path)) == "Multiline comment for test file."

def test_no_comment(tmpdir):
    file_path = tmpdir.join("test_file.py")
    file_path.write("print('Hello World')")
    assert CommentParser.get_file_purpose(str(file_path)) == "No description available"

def test_multiple_comments(tmpdir):
    file_path = tmpdir.join("test_file.py")
    file_path.write("""
    # This is not a GynTree comment
    # GynTree: This is the correct comment
    # This is another non-GynTree comment
    """)
    assert CommentParser.get_file_purpose(str(file_path)) == "This is the correct comment"

def test_html_comment(tmpdir):
    file_path = tmpdir.join("test_file.html")
    file_path.write("<!-- GynTree: HTML file comment -->")
    assert CommentParser.get_file_purpose(str(file_path)) == "HTML file comment"

def test_unsupported_file_type(tmpdir):
    file_path = tmpdir.join("test_file.xyz")
    file_path.write("GynTree: This shouldn't be parsed")
    assert CommentParser.get_file_purpose(str(file_path)) == "Unsupported file type"

def test_empty_file(tmpdir):
    file_path = tmpdir.join("empty_file.py")
    file_path.write("")
    assert CommentParser.get_file_purpose(str(file_path)) == "No description available"

def test_comment_with_special_characters(tmpdir):
    file_path = tmpdir.join("test_file.py")
    file_path.write("# GynTree: Special chars: !@#$%^&*()")
    assert CommentParser.get_file_purpose(str(file_path)) == "Special chars: !@#$%^&*()"