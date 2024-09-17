# GynTree: This module provides utilities for aggregating and formatting file/directory exclusions.
import os
from collections import defaultdict

class ExclusionAggregator:
    @staticmethod
    def aggregate_exclusions(exclusions):
        aggregated = {
            'directories': defaultdict(set),
            'files': defaultdict(set)
        }
        for exclusion_type, items in exclusions.items():
            for item in items:
                base_name = os.path.basename(item)
                parent_dir = os.path.dirname(item)
                if exclusion_type == 'directories':
                    if base_name in ['__pycache__', '.git', 'venv', '.venv', 'env', '.vs', '_internal']:
                        aggregated['directories']['common'].add(base_name)
                    elif base_name in ['build', 'dist']:
                        aggregated['directories']['build'].add(base_name)
                    else:
                        # Check if it's not a subdirectory of an already excluded directory
                        if not any(item.startswith(excluded) for excluded in aggregated['directories']['common'] | aggregated['directories']['build']):
                            aggregated['directories']['other'].add(item)
                elif exclusion_type == 'files':
                    if base_name.endswith('.pyc'):
                        aggregated['files']['pyc'].add(parent_dir)
                    elif base_name in ['.gitignore', '.dockerignore', '.vsignore', 'requirements.txt']:
                        aggregated['files']['ignore'].add(base_name)
                    elif base_name == '__init__.py':
                        aggregated['files']['init'].add(parent_dir)
                    else:
                        aggregated['files']['other'].add(item)
        return aggregated

    @staticmethod
    def format_aggregated_exclusions(aggregated):
        formatted = []
        if aggregated['directories']:
            formatted.append("Directories:")
            for category, items in aggregated['directories'].items():
                if items:
                    if category == 'common':
                        formatted.append(f"  Common: {', '.join(sorted(items))}")
                    elif category == 'build':
                        formatted.append(f"  Build: {', '.join(sorted(items))}")
                    elif category == 'other':
                        formatted.append("  Other:")
                        for item in sorted(items):
                            formatted.append(f"    - {item}")
        if aggregated['files']:
            formatted.append("Files:")
            for category, items in aggregated['files'].items():
                if items:
                    if category == 'pyc':
                        formatted.append(f"  Python Cache: {len(items)} directories with .pyc files")
                    elif category == 'ignore':
                        formatted.append(f"  Ignore Files: {', '.join(sorted(items))}")
                    elif category == 'init':
                        formatted.append(f"  __init__.py: {len(items)} directories")
                    elif category == 'other':
                        formatted.append("  Other:")
                        for item in sorted(items):
                            formatted.append(f"    - {item}")
        return "\n".join(formatted)