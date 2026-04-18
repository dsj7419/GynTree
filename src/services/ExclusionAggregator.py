import os
from collections import defaultdict
from typing import DefaultDict, Dict, List, Set, TypedDict, Union


class AggregatedDict(TypedDict):
    root_exclusions: Set[str]
    excluded_dirs: DefaultDict[str, Set[str]]
    excluded_files: DefaultDict[str, Set[str]]


class ExclusionAggregator:
    COMMON_DIRS: Set[str] = {
        "node_modules",
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "env",
        ".vs",
        "_internal",
        ".next",
        "public",
        "migrations",
    }

    BUILD_DIRS: Set[str] = {"dist", "build", "out"}

    CONFIG_FILES: Set[str] = {
        ".gitignore",
        ".dockerignore",
        ".eslintrc.cjs",
        ".npmrc",
        ".env",
        ".env.development",
        "next-env.d.ts",
        "next.config.js",
        "postcss.config.cjs",
        "prettier.config.js",
        "tailwind.config.ts",
        "tsconfig.json",
    }

    PACKAGE_FILES: Set[str] = {
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
    }

    @staticmethod
    def aggregate_exclusions(
        exclusions: Dict[str, Set[str]]
    ) -> Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]]:
        if not isinstance(exclusions, dict):
            raise ValueError("Exclusions must be a dictionary")

        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]] = {
            "root_exclusions": set(),
            "excluded_dirs": defaultdict(set),
            "excluded_files": defaultdict(set),
        }

        ExclusionAggregator._process_root_exclusions(exclusions, aggregated)
        ExclusionAggregator._process_directory_exclusions(exclusions, aggregated)
        ExclusionAggregator._process_file_exclusions(exclusions, aggregated)

        return aggregated

    @staticmethod
    def _process_root_exclusions(
        exclusions: Dict[str, Set[str]],
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
    ) -> None:
        normalized_roots = {
            os.path.normpath(item) for item in exclusions["root_exclusions"]
        }
        if isinstance(aggregated["root_exclusions"], set):
            aggregated["root_exclusions"].update(normalized_roots)

    @staticmethod
    def _process_directory_exclusions(
        exclusions: Dict[str, Set[str]],
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
    ) -> None:
        excluded_dirs = aggregated["excluded_dirs"]
        if isinstance(excluded_dirs, defaultdict):
            for item in exclusions.get("excluded_dirs", set()):
                normalized_item = os.path.normpath(item)
                base_name = os.path.basename(normalized_item)

                if base_name in ExclusionAggregator.COMMON_DIRS:
                    excluded_dirs["common"].add(base_name)
                elif base_name in ExclusionAggregator.BUILD_DIRS:
                    excluded_dirs["build"].add(base_name)
                else:
                    excluded_dirs["other"].add(normalized_item)

    @staticmethod
    def _process_file_exclusions(
        exclusions: Dict[str, Set[str]],
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
    ) -> None:
        excluded_files = aggregated["excluded_files"]
        if isinstance(excluded_files, defaultdict):
            for item in exclusions.get("excluded_files", set()):
                normalized_item = os.path.normpath(item)
                base_name = os.path.basename(normalized_item)
                ExclusionAggregator._categorize_file(
                    normalized_item, base_name, excluded_files
                )

    @staticmethod
    def _categorize_file(
        normalized_item: str,
        base_name: str,
        excluded_files: DefaultDict[str, Set[str]],
    ) -> None:
        if base_name in ExclusionAggregator.CONFIG_FILES:
            excluded_files["config"].add(base_name)
        elif normalized_item.endswith((".pyc", ".pyo", ".pyd")):
            excluded_files["cache"].add(normalized_item)
        elif base_name == "__init__.py":
            excluded_files["init"].add(os.path.dirname(normalized_item))
        elif base_name.endswith((".js", ".cjs", ".mjs", ".ts", ".tsx", ".jsx")):
            excluded_files["script"].add(base_name)
        elif base_name.endswith((".sql", ".sqlite", ".db")):
            excluded_files["database"].add(base_name)
        elif base_name.endswith((".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg")):
            excluded_files["asset"].add(base_name)
        elif base_name in ExclusionAggregator.PACKAGE_FILES:
            excluded_files["package"].add(base_name)
        elif base_name.endswith((".css", ".scss", ".less")):
            excluded_files["style"].add(base_name)
        else:
            excluded_files["other"].add(normalized_item)

    @staticmethod
    def format_aggregated_exclusions(
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]]
    ) -> str:
        formatted_sections: List[str] = []
        ExclusionAggregator._format_root_exclusions(aggregated, formatted_sections)
        ExclusionAggregator._format_directory_exclusions(aggregated, formatted_sections)
        ExclusionAggregator._format_file_exclusions(aggregated, formatted_sections)
        return "\n".join(formatted_sections)

    @staticmethod
    def _format_root_exclusions(
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
        formatted_sections: List[str],
    ) -> None:
        root_exclusions = aggregated["root_exclusions"]
        if isinstance(root_exclusions, set) and root_exclusions:
            formatted_sections.append("Root Exclusions:")
            sections = [f" - {item}" for item in sorted(root_exclusions)]
            formatted_sections.extend(sections)

    @staticmethod
    def _format_directory_exclusions(
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
        formatted_sections: List[str],
    ) -> None:
        excluded_dirs = aggregated["excluded_dirs"]
        if isinstance(excluded_dirs, defaultdict) and any(excluded_dirs.values()):
            formatted_sections.append("\nDirectories:")
            for category, items in sorted(excluded_dirs.items()):
                if items:
                    if category == "other":
                        formatted_sections.append(f" {category.capitalize()}:")
                        items_list = [f" - {item}" for item in sorted(items)]
                        formatted_sections.extend(items_list)
                    else:
                        category_str = (
                            f" {category.capitalize()}: {', '.join(sorted(items))}"
                        )
                        formatted_sections.append(category_str)

    @staticmethod
    def _format_file_exclusions(
        aggregated: Dict[str, Union[Set[str], DefaultDict[str, Set[str]]]],
        formatted_sections: List[str],
    ) -> None:
        excluded_files = aggregated["excluded_files"]
        if isinstance(excluded_files, defaultdict) and any(excluded_files.values()):
            formatted_sections.append("\nFiles:")
            for category, items in sorted(excluded_files.items()):
                if items:
                    if category in ["cache", "init"]:
                        formatted_sections.append(
                            f" {category.capitalize()}: {len(items)} items"
                        )
                    elif category == "other":
                        formatted_sections.append(f" {category.capitalize()}:")
                        other_items = [f" - {item}" for item in sorted(items)]
                        formatted_sections.extend(other_items)
                    else:
                        item_str = (
                            f" {category.capitalize()}: {', '.join(sorted(items))}"
                        )
                        formatted_sections.append(item_str)
