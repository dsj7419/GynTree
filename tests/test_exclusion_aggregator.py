import os
import pytest
from collections import defaultdict
from services.ExclusionAggregator import ExclusionAggregator

def test_aggregate_exclusions():
    exclusions = {
        'root_exclusions': {os.path.normpath('/path/to/root_exclude')},
        'excluded_dirs': {
            '/path/to/__pycache__',
            '/path/to/.git',
            '/path/to/venv',
            '/path/to/build',
            '/path/to/custom_dir'
        },
        'excluded_files': {
            '/path/to/file.pyc',
            '/path/to/.gitignore',
            '/path/to/__init__.py',
            '/path/to/custom_file.txt'
        }
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    
    assert 'root_exclusions' in aggregated
    assert 'excluded_dirs' in aggregated
    assert 'excluded_files' in aggregated
    
    assert os.path.normpath('/path/to/root_exclude') in aggregated['root_exclusions']
    assert 'common' in aggregated['excluded_dirs']
    assert 'build' in aggregated['excluded_dirs']
    assert 'other' in aggregated['excluded_dirs']
    assert 'cache' in aggregated['excluded_files']
    assert 'config' in aggregated['excluded_files']
    assert 'init' in aggregated['excluded_files']
    assert 'other' in aggregated['excluded_files']
    
    assert '__pycache__' in aggregated['excluded_dirs']['common']
    assert '.git' in aggregated['excluded_dirs']['common']
    assert 'venv' in aggregated['excluded_dirs']['common']
    assert 'build' in aggregated['excluded_dirs']['build']
    assert '/path/to/custom_dir' in aggregated['excluded_dirs']['other']
    assert '/path/to' in aggregated['excluded_files']['cache']
    assert '.gitignore' in aggregated['excluded_files']['config']
    assert '/path/to' in aggregated['excluded_files']['init']
    assert '/path/to/custom_file.txt' in aggregated['excluded_files']['other']

def test_format_aggregated_exclusions():
    aggregated = {
        'root_exclusions': {'/path/to/root_exclude'},
        'excluded_dirs': {
            'common': {'__pycache__', '.git', 'venv'},
            'build': {'build', 'dist'},
            'other': {'/path/to/custom_dir'}
        },
        'excluded_files': {
            'cache': {'/path/to'},
            'config': {'.gitignore', '.dockerignore'},
            'init': {'/path/to'},
            'other': {'/path/to/custom_file.txt'}
        }
    }
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    formatted_lines = formatted.split('\n')
    
    assert "Root Exclusions:" in formatted_lines
    assert " - /path/to/root_exclude" in formatted_lines
    assert "Directories:" in formatted_lines
    assert " Common: __pycache__, .git, venv" in formatted_lines
    assert " Build: build, dist" in formatted_lines
    assert " Other:" in formatted_lines
    assert "  - /path/to/custom_dir" in formatted_lines
    assert "Files:" in formatted_lines
    assert " Cache: 1 items" in formatted_lines
    assert " Config: .dockerignore, .gitignore" in formatted_lines
    assert " Init: 1 items" in formatted_lines
    assert " Other:" in formatted_lines
    assert "  - /path/to/custom_file.txt" in formatted_lines

def test_empty_exclusions():
    exclusions = {'root_exclusions': set(), 'excluded_dirs': set(), 'excluded_files': set()}
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    assert aggregated == {'root_exclusions': set(), 'excluded_dirs': defaultdict(set), 'excluded_files': defaultdict(set)}
    assert formatted == ""

def test_only_common_exclusions():
    exclusions = {
        'root_exclusions': set(),
        'excluded_dirs': {'/path/to/__pycache__', '/path/to/.git', '/path/to/venv'},
        'excluded_files': {'/path/to/.gitignore'}
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    assert 'common' in aggregated['excluded_dirs']
    assert 'config' in aggregated['excluded_files']
    assert "Common: __pycache__, .git, venv" in formatted
    assert "Config: .gitignore" in formatted

def test_complex_directory_structure():
    exclusions = {
        'root_exclusions': {'/project/.git'},
        'excluded_dirs': {
            '/project/backend/__pycache__',
            '/project/frontend/node_modules',
            '/project/docs/build',
            '/project/tests/.pytest_cache'
        },
        'excluded_files': {
            '/project/.env',
            '/project/backend/config.pyc',
            '/project/frontend/package-lock.json'
        }
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert len(aggregated['root_exclusions']) == 1
    assert len(aggregated['excluded_dirs']['common']) == 3  # __pycache__, node_modules, .pytest_cache
    assert len(aggregated['excluded_dirs']['build']) == 1  # build
    assert len(aggregated['excluded_files']['cache']) == 1  # .pyc
    assert len(aggregated['excluded_files']['config']) == 1  # .env
    assert len(aggregated['excluded_files']['package']) == 1  # package-lock.json
    
    assert "Root Exclusions:" in formatted
    assert " - /project/.git" in formatted
    assert "Common: __pycache__, .pytest_cache, node_modules" in formatted
    assert "Build: build" in formatted
    assert "Cache: 1 items" in formatted
    assert "Config: .env" in formatted
    assert "Package: package-lock.json" in formatted

def test_nested_exclusions():
    exclusions = {
        'root_exclusions': {'/project/nested'},
        'excluded_dirs': {
            '/project/nested/inner/__pycache__',
            '/project/nested/inner/node_modules'
        },
        'excluded_files': {
            '/project/nested/inner/.env',
            '/project/nested/inner/config.pyc'
        }
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert len(aggregated['root_exclusions']) == 1
    assert len(aggregated['excluded_dirs']) == 0  # All should be under root exclusions
    assert len(aggregated['excluded_files']) == 0  # All should be under root exclusions
    
    assert "Root Exclusions:" in formatted
    assert " - /project/nested" in formatted
    assert "Directories:" not in formatted
    assert "Files:" not in formatted

def test_exclusion_priority():
    exclusions = {
        'root_exclusions': {'/project/root_exclude'},
        'excluded_dirs': {
            '/project/root_exclude/subdir',
            '/project/other_dir'
        },
        'excluded_files': {
            '/project/root_exclude/file.txt',
            '/project/other_file.txt'
        }
    }
    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    
    assert '/project/root_exclude' in aggregated['root_exclusions']
    assert '/project/root_exclude/subdir' not in aggregated['excluded_dirs'].get('other', set())
    assert '/project/root_exclude/file.txt' not in aggregated['excluded_files'].get('other', set())
    assert '/project/other_dir' in aggregated['excluded_dirs'].get('other', set())
    assert '/project/other_file.txt' in aggregated['excluded_files'].get('other', set())
    
    assert "Root Exclusions:" in formatted
    assert " - /project/root_exclude" in formatted
    assert "Directories:" in formatted
    assert " Other:" in formatted
    assert "  - /project/other_dir" in formatted
    assert "Files:" in formatted
    assert " Other:" in formatted
    assert "  - /project/other_file.txt" in formatted