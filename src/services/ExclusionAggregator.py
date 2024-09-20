import os
from collections import defaultdict
from typing import Dict, Set

class ExclusionAggregator:
    @staticmethod
    def aggregate_exclusions(exclusions: Dict[str, Set[str]]) -> Dict[str, Dict[str, Set[str]]]:
        aggregated = {
            'root_exclusions': set(),
            'excluded_dirs': defaultdict(set),
            'excluded_files': defaultdict(set)
        }

        root_exclusions = exclusions.get('root_exclusions', set())
        for item in root_exclusions:
            aggregated['root_exclusions'].add(os.path.normpath(item))

        for exclusion_type, items in exclusions.items():
            if exclusion_type == 'root_exclusions':
                continue 

            for item in items:
                normalized_item = os.path.normpath(item)
                
                if any(normalized_item.startswith(root_dir) for root_dir in root_exclusions):
                    continue

                base_name = os.path.basename(normalized_item)
                parent_dir = os.path.dirname(normalized_item)

                if exclusion_type == 'excluded_dirs':
                    if base_name in ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'env', '.vs', '_internal', '.next', 'public', 'dist', 'build', 'out', 'migrations']:
                        aggregated['excluded_dirs']['common'].add(base_name)
                    elif base_name in ['prisma', 'src', 'components', 'pages', 'api']:
                        aggregated['excluded_dirs']['app structure'].add(base_name)
                    else:
                        aggregated['excluded_dirs']['other'].add(base_name)
                elif exclusion_type == 'excluded_files':
                    if normalized_item.endswith(('.pyc', '.pyo', '.pyd')):
                        aggregated['excluded_files']['cache'].add(normalized_item)
                    elif base_name in ['.gitignore', '.dockerignore', '.eslintrc.cjs', '.npmrc', '.env', '.env.development', 'next-env.d.ts', 'next.config.js', 'postcss.config.cjs', 'prettier.config.js', 'tailwind.config.ts', 'tsconfig.json']:
                        aggregated['excluded_files']['config'].add(base_name)
                    elif base_name == '__init__.py':
                        aggregated['excluded_files']['init'].add(parent_dir)
                    elif base_name.endswith(('.js', '.cjs', '.mjs', '.ts', '.tsx', '.jsx')):
                        aggregated['excluded_files']['script'].add(base_name)
                    elif base_name.endswith(('.sql', '.sqlite', '.db')):
                        aggregated['excluded_files']['database'].add(base_name)
                    elif base_name.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                        aggregated['excluded_files']['asset'].add(base_name)
                    elif base_name in ['package.json', 'pnpm-lock.yaml', 'yarn.lock', 'package-lock.json']:
                        aggregated['excluded_files']['package'].add(base_name)
                    elif base_name.endswith(('.md', '.txt')):
                        aggregated['excluded_files']['document'].add(base_name)
                    elif base_name.endswith(('.css', '.scss', '.less')):
                        aggregated['excluded_files']['style'].add(base_name)
                    else:
                        aggregated['excluded_files']['other'].add(base_name)

        return aggregated

    @staticmethod
    def format_aggregated_exclusions(aggregated: Dict[str, Dict[str, Set[str]]]) -> str:
        formatted = []

        if aggregated['root_exclusions']:
            formatted.append("Root Exclusions:")
            for item in sorted(aggregated['root_exclusions']):
                formatted.append(f" - {item}")

        if aggregated['excluded_dirs']:
            formatted.append("\nDirectories:")
            for category, items in aggregated['excluded_dirs'].items():
                if items:
                    formatted.append(f" {category.capitalize()}: {', '.join(sorted(items))}")

        if aggregated['excluded_files']:
            formatted.append("\nFiles:")
            for category, items in aggregated['excluded_files'].items():
                if items:
                    if category in ['cache', 'init']:
                        formatted.append(f" {category.capitalize()}: {len(items)} items")
                    else:
                        formatted.append(f" {category.capitalize()}: {len(items)} items")
                        if category == 'other' and len(items) <= 5:
                            for item in sorted(items):
                                formatted.append(f"  - {item}")

        return "\n".join(formatted)