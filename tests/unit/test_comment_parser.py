import pytest
import logging
from services.CommentParser import CommentParser, DefaultFileReader, DefaultCommentSyntax

pytestmark = pytest.mark.unit

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
    assert comment_parser.get_file_purpose(str(file_path)) == "This is a multiline comment\nin a JavaScript file."

def test_multiline_comment_cpp(tmpdir, comment_parser):
    file_content = """
    /* GynTree: This C++ multiline comment
       spans multiple lines.
    */
    """
    file_path = tmpdir.join("test_file.cpp")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This C++ multiline comment\nspans multiple lines."

def test_multiline_comment_python(tmpdir, comment_parser):
    file_content = '''
    """
    GynTree: This file contains the ProjectManager class, which handles project-related operations.
    It manages creating, loading, and saving projects, as well as maintaining project metadata.
    """
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This file contains the ProjectManager class, which handles project-related operations.\nIt manages creating, loading, and saving projects, as well as maintaining project metadata."

def test_multiline_comment_python_complex(tmpdir, comment_parser):
    file_content = '''
    """
    GynTree: ProjectController manages the loading, saving, and setting of projects.
    This controller handles the main project-related operations, ensuring that the
    current project is properly set up and context is established. It interacts with
    the ProjectManager and ProjectContext services to manage the lifecycle of a project
    within the application.

    Responsibilities:
    - Load and save projects using the ProjectManager.
    - Set the current project and initialize the project context.
    - Provide project-related information to the main UI.
    """
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    expected = '''ProjectController manages the loading, saving, and setting of projects.
This controller handles the main project-related operations, ensuring that the
current project is properly set up and context is established. It interacts with
the ProjectManager and ProjectContext services to manage the lifecycle of a project
within the application.

Responsibilities:
- Load and save projects using the ProjectManager.
- Set the current project and initialize the project context.
- Provide project-related information to the main UI.'''
    assert comment_parser.get_file_purpose(str(file_path)) == expected

def test_multiline_comment_python_with_leading_gyntree(tmpdir, comment_parser):
    file_content = '''
    """
    GynTree: UIController manages the interaction between the project and the UI.
    This controller is responsible for updating and resetting UI components whenever
    a new project is loaded or created. It ensures that the correct project information
    is displayed and that the user interface reflects the current project state.

    Responsibilities:
    - Reset and update UI components like directory tree, exclusions, and analysis.
    - Manage exclusion-related UI elements.
    - Provide a clean interface for displaying project information in the main UI.
    """
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    expected = '''UIController manages the interaction between the project and the UI.
This controller is responsible for updating and resetting UI components whenever
a new project is loaded or created. It ensures that the correct project information
is displayed and that the user interface reflects the current project state.

Responsibilities:
- Reset and update UI components like directory tree, exclusions, and analysis.
- Manage exclusion-related UI elements.
- Provide a clean interface for displaying project information in the main UI.'''
    assert comment_parser.get_file_purpose(str(file_path)) == expected

def test_no_comment(tmpdir, comment_parser):
    file_path = tmpdir.join("test_file.py")
    file_path.write("print('Hello World')")
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
    file_path.write("GynTree: Not parsed")
    assert comment_parser.get_file_purpose(str(file_path)) == "Unsupported file type"

def test_empty_file(tmpdir, comment_parser):
    file_path = tmpdir.join("empty_file.py")
    file_path.write("")
    assert comment_parser.get_file_purpose(str(file_path)) == "File found empty"

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

def test_unsupported_file_type_logging(tmpdir, comment_parser, caplog):
    file_path1 = tmpdir.join("test_file1.xyz")
    file_path1.write("GynTree: Not parsed")
    file_path2 = tmpdir.join("test_file2.xyz")
    file_path2.write("GynTree: Not parsed either")
    with caplog.at_level(logging.DEBUG):
        comment_parser.get_file_purpose(str(file_path1))
        comment_parser.get_file_purpose(str(file_path2))
    assert len([record for record in caplog.records if "Unsupported file type: .xyz" in record.message]) == 2

def test_long_file(tmpdir, comment_parser):
    lines = [f'# line {i}' for i in range(1000)]
    lines.insert(0, '# GynTree: Description in long file')
    file_content = '\n'.join(lines)
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "Description in long file"

def test_multiline_comment_with_code(tmpdir, comment_parser):
    file_content = '''
    """
    GynTree: This is a multiline comment with code examples.

    Example:
    def example_function():
        return "Hello, World!"
    
    This function returns a greeting.
    """
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    expected = '''This is a multiline comment with code examples.

Example:
def example_function():
    return "Hello, World!"

This function returns a greeting.'''
    assert comment_parser.get_file_purpose(str(file_path)) == expected

def test_comment_after_code(tmpdir, comment_parser):
    file_content = '''
    import sys
    
    # GynTree: This comment comes after some code
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This comment comes after some code"

def test_multiple_gyntree_comments(tmpdir, comment_parser):
    file_content = '''
    # GynTree: First comment
    print("Some code")
    # GynTree: Second comment
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "First comment"

def test_python_file_with_code_and_comments(tmpdir, comment_parser):
    file_content = '''
    # GynTree: This is a file-level comment
    
    def example_function():
        """
        GynTree: This is a docstring comment
        It should be captured correctly
        """
        # This is a regular comment, not a GynTree comment
        pass

    # GynTree: Another file-level comment
    class ExampleClass:
        pass
    '''
    file_path = tmpdir.join("test_file.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This is a file-level comment"

def test_comment_parser_self_parse(tmpdir, comment_parser):
    file_content = '''
    class CommentParser:
        def __init__(self, file_reader, comment_syntax):
            self.file_reader = file_reader
            self.comment_syntax = comment_syntax
            # GynTree: This is a comment within the CommentParser class
            self.gyntree_pattern = re.compile(r'gyntree:', re.IGNORECASE)

    def some_other_function():
        # This should not be captured
        pass
    '''
    file_path = tmpdir.join("comment_parser.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This is a comment within the CommentParser class"

def test_comment_parser_edge_cases(tmpdir, comment_parser):
    file_content = '''
    # This is a regular comment
    # GynTree: This is the first GynTree comment
    """
    This is a multiline string, not a comment
    GynTree: This should not be captured
    """
    # GynTree: This is the second GynTree comment
    def some_function():
        """
        GynTree: This is a docstring GynTree comment
        It should be captured if it's the first GynTree comment in the file
        """
        pass
    '''
    file_path = tmpdir.join("edge_case_test.py")
    file_path.write(file_content)
    assert comment_parser.get_file_purpose(str(file_path)) == "This is the first GynTree comment"
