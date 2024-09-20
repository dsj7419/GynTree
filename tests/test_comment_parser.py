import pytest
from services.CommentParser import CommentParser, DefaultFileReader, DefaultCommentSyntax

@pytest.fixture
def comment_parser():
    return CommentParser(DefaultFileReader(), DefaultCommentSyntax())

def test_single_line_comment(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.py")
    file_path.write("# GynTree: This is a test file.")
    assert comment_parser.get_file_purpose(str(file_path)) == "This is a test file."

def test_multiline_comment_js(tmpdir, comment_parser):
    file_content = """
    /*
     * GynTree: This is a multiline comment
     * in a JavaScript file.
     */
    """
    file_path = tmpdir.join("test_file.js")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This is a multiline comment in a JavaScript file."

def test_multiline_comment_cpp(tmpdir, comment_parser):
    file_content = """
    /* GynTree: This C++ multiline comment
       spans multiple lines. */
    """
    file_path = tmpdir.join("test_file.cpp")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This C++ multiline comment spans multiple lines."

def test_no_comment(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.py")
    file_path.write("print('Hello world')")
    assert comment_parser.get_file_purpose(str(file_path)) == "No description available"

def test_multiple_comments(tmpdir, comment_parser):
    file_content = """
    # Non-GynTree comment
    # GynTree: First GynTree comment
    # GynTree: Second GynTree comment
    """
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "First GynTree comment"

def test_html_comment(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.html")
    file_path.write("<!-- GynTree: HTML file comment -->")
    assert comment_parser.get_file_purpose(str(file_path)) == "HTML file comment"

def test_unsupported_file_type(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.xyz")
    file_path.write("GynTree: This should not be parsed")
    assert comment_parser.get_file_purpose(str(file_path)) == "Unsupported file type"

def test_empty_file(tmpdir, comment_parser):
    file_path = tmpdir.join("empty_file.py")
    file_path.write("")
    assert comment_parser.get_file_purpose(str(file_path)) == "File not found or empty"

def test_comment_with_special_characters(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.py")
    file_path.write("# GynTree: Special chars: !@#$%^&*()")
    assert comment_parser.get_file_purpose(str(file_path)) == "Special chars: !@#$%^&*()"

def test_case_insensitive_gyntree(tmpdir, comment_parser):
    file_content = "# gyntree: Case insensitive test"
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "Case insensitive test"

def test_gyntree_not_at_start_of_line(tmpdir, comment_parser):
    file_content = """
    /*
     * Introduction
     * GynTree: Description text
     */
    """
    file_path = tmpdir.join("test_file.js")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "Description text"

'''def test_long_file(tmpdir, comment_parser):
    lines = ['# Line {}'.format(i) for i in range(1000)]
    lines.insert(500, '# GynTree: Description in long file')
    file_content = '\n'.join(lines)
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "Description in long file"'''