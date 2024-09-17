# GynTree: Implements functionality for parsing and extracting comments from various file types.

import os
import re

class CommentParser:
    COMMENT_SYNTAX = {
        '.py': ('#', '"""'),
        '.js': ('//', '/*'),
        '.ts': ('//', '/*'),
        '.tsx': ('//', '/*'),
        '.html': ('<!--', '<!--'),
        '.css': ('/*', '/*'),
        '.java': ('//', '/*'),
        '.c': ('//', '/*'),
        '.cpp': ('//', '/*'),
    }

    def get_file_purpose(self, filepath):
        file_extension = os.path.splitext(filepath)[1].lower()

        if file_extension not in self.COMMENT_SYNTAX:
            return "Unsupported file type"

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read(1000) 
                lines = content.split('\n')[:20]
                
                single_line, multi_line = self.COMMENT_SYNTAX[file_extension]

                multi_line_pattern = re.compile(rf'{re.escape(multi_line)}(.*?)GynTree:(.*?)({re.escape(multi_line)})', re.DOTALL)
                multi_line_match = multi_line_pattern.search(content)

                if multi_line_match:
                    return multi_line_match.group(2).strip()
                
                for line in lines:
                    if line.strip().startswith(single_line) and "GynTree:" in line:
                        return self._extract_gyntree_comment(line.strip().lstrip(single_line).strip())

                return "No description available"

        except FileNotFoundError:
            return "File not found"
        except UnicodeDecodeError:
            return "Unable to decode file"

    def _extract_gyntree_comment(self, comment):
        comment = comment.strip().strip('"').strip("'")
        
        if "GynTree:" in comment:
            return comment.split("GynTree:", 1)[1].strip()
        
        return "No description available"