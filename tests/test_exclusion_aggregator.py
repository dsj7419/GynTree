"""
GynTree: This file contains unit tests for the ExclusionAggregator class,
ensuring proper aggregation and formatting of exclusion rules.
"""

from collections import defaultdict
import pytest
from services.ExclusionAggregator import ExclusionAggregator

def test_aggregate_exclusions():
    exclusions = {
        'directories': [
            '/path/to/__pycache__',
            '/path/to/.git',
            '/path/to/venv',
            '/path/to/build',
            '/path/to/custom_dir'
        ],
        'files': [
            '/path/to/file.pyc',
            '/path/to/.gitignore',
            '/path/to/__init__.py',
            '/path/to/custom_file.txt'
        ]
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)

    assert 'common' in aggregated['directories']
    assert 'build' in aggregated['directories']
    assert 'other' in aggregated['directories']
    assert 'pyc' in aggregated['files']
    assert 'ignore' in aggregated['files']
    assert 'init' in aggregated['files']
    assert 'other' in aggregated['files']

    assert '__pycache__' in aggregated['directories']['common']
    assert '.git' in aggregated['directories']['common']
    assert 'venv' in aggregated['directories']['common']
    assert 'build' in aggregated['directories']['build']
    assert '/path/to/custom_dir' in aggregated['directories']['other']
    assert '/path/to' in aggregated['files']['pyc']
    assert '.gitignore' in aggregated['files']['ignore']
    assert '/path/to' in aggregated['files']['init']
    assert '/path/to/custom_file.txt' in aggregated['files']['other']

def test_format_aggregated_exclusions():
    aggregated = {
        'directories': {
            'common': {'__pycache__', '.git', 'venv'},
            'build': {'build', 'dist'},
            'other': {'/path/to/custom_dir'}
        },
        'files': {
            'pyc': {'/path/to'},
            'ignore': {'.gitignore', '.dockerignore'},
            'init': {'/path/to'},
            'other': {'/path/to/custom_file.txt'}
        }
    }

    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    formatted_lines = formatted.split('\n')

    assert "Directories:" in formatted_lines
    assert "  Common: __pycache__, .git, venv" in formatted_lines
    assert "  Build: build, dist" in formatted_lines
    assert "  Other:" in formatted_lines
    assert "    - /path/to/custom_dir" in formatted_lines
    assert "Files:" in formatted_lines
    assert "  Python Cache: 1 directories with .pyc files" in formatted_lines
    assert "  Ignore Files: .dockerignore, .gitignore" in formatted_lines
    assert "  __init__.py: 1 directories" in formatted_lines
    assert "  Other:" in formatted_lines
    assert "    - /path/to/custom_file.txt" in formatted_lines

def test_empty_exclusions():
    exclusions = {'directories': [], 'files': []}
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert aggregated == {'directories': defaultdict(set), 'files': defaultdict(set)}
    assert formatted == ""

def test_only_common_exclusions():
    exclusions = {
        'directories': ['/path/to/__pycache__', '/path/to/.git', '/path/to/venv'],
        'files': ['/path/to/.gitignore']
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert 'other' not in aggregated['directories']
    assert 'other' not in aggregated['files']
    assert "Common: __pycache__, .git, venv" in formatted
    assert "Ignore Files: .gitignore" in formatted

def test_complex_directory_structure():
    exclusions = {
        'directories': [
            '/project/backend/__pycache__',
            '/project/frontend/node_modules',
            '/project/.git',
            '/project/docs/build',
            '/project/tests/.pytest_cache'
        ],
        'files': [
            '/project/.env',
            '/project/backend/config.pyc',
            '/project/frontend/package-lock.json'
        ]
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert len(aggregated['directories']['common']) == 3  # __pycache__, .git, node_modules
    assert len(aggregated['directories']['build']) == 1  # build
    assert len(aggregated['directories']['other']) == 1  # .pytest_cache
    assert len(aggregated['files']['pyc']) == 1
    assert len(aggregated['files']['other']) == 2  # .env and package-lock.json
    
    assert "Common: __pycache__, .git, node_modules" in formatted
    assert "Build: build" in formatted
    assert ".pytest_cache" in formatted
    assert "Python Cache: 1 directories with .pyc files" in formatted
    assert ".env" in formatted
    assert "package-lock.json" in formatted