import os
import re

class CommentParser:
    COMMENT_SYNTAX = {
        '.py': ('#', '"""'),     # Python
        '.js': ('//', '/*'),     # JavaScript
        '.ts': ('//', '/*'),     # TypeScript
        '.tsx': ('//', '/*'),    # TypeScript (React)
        '.html': ('<!--', '<!--'),  # HTML
        '.css': ('/*', '/*'),    # CSS
        '.java': ('//', '/*'),   # Java
        '.c': ('//', '/*'),      # C
        '.cpp': ('//', '/*'),    # C++
    }

    @staticmethod
    def get_file_purpose(filepath):
        """
        Extract file purpose from the top comment in various formats.
        Limit scanning to the first 20 lines for performance.
        """
        file_extension = os.path.splitext(filepath)[1].lower()

        if file_extension not in CommentParser.COMMENT_SYNTAX:
            return "Unsupported file type"

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read(1000)  # Read first 1000 characters
                lines = content.split('\n')[:20]  # Limit to first 20 lines
                
                single_line, multi_line = CommentParser.COMMENT_SYNTAX[file_extension]

                # Check for multi-line comment with GynTree
                multi_line_pattern = re.compile(rf'{re.escape(multi_line)}(.*?)GynTree:(.*?)({re.escape(multi_line)})', re.DOTALL)
                multi_line_match = multi_line_pattern.search(content)

                if multi_line_match:
                    comment = multi_line_match.group(2).strip()
                    return comment
                
                # Check for single-line comments with GynTree
                comment = next((line.strip().lstrip(single_line).strip() for line in lines 
                                if line.strip().startswith(single_line) and "GynTree:" in line), 
                               "No description available")
                
                return CommentParser.extract_gyntree_comment(comment)

        except FileNotFoundError:
            return "No description available"
        except UnicodeDecodeError:
            return "Unable to decode file"

    @staticmethod
    def extract_gyntree_comment(comment):
        """
        Extract the GynTree comment from the given comment string.
        Handles various formats of GynTree comments.
        """
        comment = comment.strip().strip('"').strip("'")
        
        if "GynTree:" in comment:
            gyntree_comment = comment.split("GynTree:", 1)[1].strip()
            return gyntree_comment
        
        return "No description available"
