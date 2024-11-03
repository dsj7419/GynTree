"""Script to check documentation files for common issues."""
import os
import sys
from pathlib import Path

def check_docs():
    """Check documentation files for common issues."""
    docs_dir = Path("docs")
    errors_found = False
    
    # Check for required files
    required_files = [
        "index.md",
        "getting-started/installation.md",
        "getting-started/faq.md",
        "user-guide/basic-usage.md",
        "user-guide/configuration.md",
        "api/overview.md",
        "contributing/guidelines.md",
        "changelog.md"
    ]
    
    for file_path in required_files:
        full_path = docs_dir / file_path
        if not full_path.exists():
            print(f"Error: Required file missing: {file_path}")
            errors_found = True
        else:
            # Check if file has content
            content = full_path.read_text()
            if not content.strip():
                print(f"Error: File is empty: {file_path}")
                errors_found = True
            
            # Check for broken internal links
            links = [line for line in content.split("\n") if "[" in line and "]" in line]
            for link in links:
                if "](/" in link:  # Internal link
                    link_path = link.split("](")[-1].split(")")[0].lstrip("/")
                    if not (docs_dir / link_path).exists():
                        print(f"Error: Broken internal link in {file_path}: {link_path}")
                        errors_found = True
    
    return 0 if not errors_found else 1

if __name__ == "__main__":
    sys.exit(check_docs())