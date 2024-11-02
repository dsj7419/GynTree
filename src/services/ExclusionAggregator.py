import os
from collections import defaultdict
from typing import Dict, Set

class ExclusionAggregator:
    @staticmethod
    def aggregate_exclusions(exclusions: Dict[str, Set[str]]) -> Dict[str, Dict[str, Set[str]]]:
        # Input validation
        if not isinstance(exclusions, dict):
            raise ValueError("Exclusions must be a dictionary")

        # Initialize with empty categories
        aggregated = {
            'root_exclusions': set(),
            'excluded_dirs': defaultdict(set),
            'excluded_files': defaultdict(set)
        }

        # Process root exclusions first
        normalized_roots = {os.path.normpath(item) for item in exclusions['root_exclusions']}
        aggregated['root_exclusions'].update(normalized_roots)

        # Process directory exclusions
        for item in exclusions.get('excluded_dirs', set()):
            normalized_item = os.path.normpath(item)
            base_name = os.path.basename(normalized_item)
            
            # Common directories
            if base_name in ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'env', '.vs', 
                           '_internal', '.next', 'public', 'migrations']:
                aggregated['excluded_dirs']['common'].add(base_name)
            # Build directories
            elif base_name in ['dist', 'build', 'out']:
                aggregated['excluded_dirs']['build'].add(base_name)
            else:
                # For 'other' category, store the full path
                aggregated['excluded_dirs']['other'].add(normalized_item)

        # Process file exclusions
        for item in exclusions.get('excluded_files', set()):
            normalized_item = os.path.normpath(item)
            base_name = os.path.basename(normalized_item)

            # Config files
            if base_name in ['.gitignore', '.dockerignore', '.eslintrc.cjs', '.npmrc', '.env', 
                           '.env.development', 'next-env.d.ts', 'next.config.js', 'postcss.config.cjs', 
                           'prettier.config.js', 'tailwind.config.ts', 'tsconfig.json']:
                aggregated['excluded_files']['config'].add(base_name)
            elif normalized_item.endswith(('.pyc', '.pyo', '.pyd')):
                aggregated['excluded_files']['cache'].add(normalized_item)
            elif base_name == '__init__.py':
                aggregated['excluded_files']['init'].add(os.path.dirname(normalized_item))
            elif base_name.endswith(('.js', '.cjs', '.mjs', '.ts', '.tsx', '.jsx')):
                aggregated['excluded_files']['script'].add(base_name)
            elif base_name.endswith(('.sql', '.sqlite', '.db')):
                aggregated['excluded_files']['database'].add(base_name)
            elif base_name.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                aggregated['excluded_files']['asset'].add(base_name)
            elif base_name in ['package.json', 'pnpm-lock.yaml', 'yarn.lock', 'package-lock.json']:
                aggregated['excluded_files']['package'].add(base_name)
            elif base_name.endswith(('.css', '.scss', '.less')):
                aggregated['excluded_files']['style'].add(base_name)
            else:
                # For 'other' category, store the full path
                aggregated['excluded_files']['other'].add(normalized_item)

        return aggregated

    @staticmethod
    def format_aggregated_exclusions(aggregated: Dict[str, Dict[str, Set[str]]]) -> str:
        formatted = []

        # Format root exclusions
        if aggregated['root_exclusions']:
            formatted.append("Root Exclusions:")
            for item in sorted(aggregated['root_exclusions']):
                formatted.append(f" - {item}")

        # Format directories
        if any(aggregated['excluded_dirs'].values()):
            formatted.append("\nDirectories:")
            for category, items in sorted(aggregated['excluded_dirs'].items()):
                if items:
                    if category == 'other':
                        formatted.append(f" {category.capitalize()}:")
                        for item in sorted(items):
                            formatted.append(f" - {item}")
                    else:
                        formatted.append(f" {category.capitalize()}: {', '.join(sorted(items))}")

        # Format files
        if any(aggregated['excluded_files'].values()):
            formatted.append("\nFiles:")
            for category, items in sorted(aggregated['excluded_files'].items()):
                if items:
                    if category in ['cache', 'init']:
                        formatted.append(f" {category.capitalize()}: {len(items)} items")
                    elif category == 'other':
                        formatted.append(f" {category.capitalize()}:")
                        for item in sorted(items):
                            formatted.append(f" - {item}")
                    else:
                        formatted.append(f" {category.capitalize()}: {', '.join(sorted(items))}")

        return "\n".join(formatted)