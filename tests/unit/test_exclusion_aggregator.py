import os
import pytest
from collections import defaultdict
from services.ExclusionAggregator import ExclusionAggregator

pytestmark = pytest.mark.unit

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
    assert 'build' in aggregated['excluded_dirs']['common']
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
    assert " - /path/to/custom_dir" in formatted_lines
    assert "Files:" in formatted_lines
    assert " Cache: 1 items" in formatted_lines
    assert " Config: .dockerignore, .gitignore" in formatted_lines
    assert " Init: 1 items" in formatted_lines
    assert " Other:" in formatted_lines
    assert " - /path/to/custom_file.txt" in formatted_lines

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