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
