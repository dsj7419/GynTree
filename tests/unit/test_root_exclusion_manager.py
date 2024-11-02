import pytest
import os
from pathlib import Path
import logging
import psutil
import gc
from typing import Dict, Set

from services.RootExclusionManager import RootExclusionManager

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)

class RootExclusionTestHelper:
    """Helper class for RootExclusionManager testing"""
    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None
        self.manager = RootExclusionManager()

    def create_project_structure(self, project_type: str) -> None:
        """Create test project structure"""
        if project_type == "python":
            (self.tmpdir / "venv").mkdir(exist_ok=True)
            (self.tmpdir / "__pycache__").mkdir(exist_ok=True)
            (self.tmpdir / ".pytest_cache").mkdir(exist_ok=True)
            (self.tmpdir / "tests").mkdir(exist_ok=True)
            (self.tmpdir / "tests" / "__init__.py").touch()

        elif project_type == "javascript":
            (self.tmpdir / "node_modules").mkdir(exist_ok=True)
            (self.tmpdir / "dist").mkdir(exist_ok=True)
            (self.tmpdir / "build").mkdir(exist_ok=True)

        elif project_type == "nextjs":
            (self.tmpdir / ".next").mkdir(exist_ok=True)
            (self.tmpdir / "node_modules").mkdir(exist_ok=True)
            (self.tmpdir / "out").mkdir(exist_ok=True)

        elif project_type == "database":
            (self.tmpdir / "prisma").mkdir(exist_ok=True)
            (self.tmpdir / "migrations").mkdir(exist_ok=True)

    def track_memory(self) -> None:
        """Start memory tracking"""
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        """Check memory usage after operation"""
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 10 * 1024 * 1024:  # 10MB threshold
                logger.warning(f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.fixture
def helper(tmpdir):
    """Create test helper instance"""
    return RootExclusionTestHelper(Path(tmpdir))

@pytest.mark.timeout(30)
def test_default_exclusions(helper):
    """Test default exclusions are present"""
    helper.track_memory()
    
    assert '.git' in helper.manager.default_exclusions
    
    helper.check_memory_usage("default exclusions")

@pytest.mark.timeout(30)
def test_get_root_exclusions_python(helper):
    """Test Python project exclusions"""
    helper.track_memory()
    
    helper.create_project_structure("python")
    project_info = {'python': True, 'web': False}
    
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    assert 'venv' in exclusions
    assert '__pycache__' in exclusions
    assert '.pytest_cache' in exclusions
    
    helper.check_memory_usage("python exclusions")

@pytest.mark.timeout(30)
def test_get_root_exclusions_javascript(helper):
    """Test JavaScript project exclusions"""
    helper.track_memory()
    
    helper.create_project_structure("javascript")
    project_info = {'javascript': True, 'web': True}
    
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    assert 'node_modules' in exclusions
    assert 'dist' in exclusions
    assert 'build' in exclusions
    
    helper.check_memory_usage("javascript exclusions")

@pytest.mark.timeout(30)
def test_get_root_exclusions_nextjs(helper):
    """Test Next.js project exclusions"""
    helper.track_memory()
    
    helper.create_project_structure("nextjs")
    project_info = {'nextjs': True, 'javascript': True}
    
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    assert '.next' in exclusions
    assert 'node_modules' in exclusions
    assert 'out' in exclusions
    
    helper.check_memory_usage("nextjs exclusions")

@pytest.mark.timeout(30)
def test_get_root_exclusions_database(helper):
    """Test database project exclusions"""
    helper.track_memory()
    
    helper.create_project_structure("database")
    project_info = {'database': True}
    
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    assert 'prisma' in exclusions
    assert 'migrations' in exclusions
    
    helper.check_memory_usage("database exclusions")

@pytest.mark.timeout(30)
def test_merge_with_existing_exclusions(helper):
    """Test merging existing exclusions with new ones"""
    helper.track_memory()
    
    existing = {'venv', 'custom_exclude'}
    new = {'node_modules', 'venv', 'dist'}
    
    merged = helper.manager.merge_with_existing_exclusions(existing, new)
    
    assert 'custom_exclude' in merged
    assert 'node_modules' in merged
    assert 'venv' in merged
    assert 'dist' in merged
    assert len(merged) == 4
    
    helper.check_memory_usage("merge exclusions")

@pytest.mark.timeout(30)
def test_add_project_type_exclusion(helper):
    """Test adding project type exclusions"""
    helper.track_memory()
    
    project_type = 'custom_type'
    exclusions = {'custom_folder', 'custom_cache'}
    
    helper.manager.add_project_type_exclusion(project_type, exclusions)
    
    assert project_type in helper.manager.project_type_exclusions
    assert exclusions.issubset(helper.manager.project_type_exclusions[project_type])
    
    helper.check_memory_usage("add exclusions")

@pytest.mark.timeout(30)
def test_remove_project_type_exclusion(helper):
    """Test removing project type exclusions"""
    helper.track_memory()
    
    # Setup initial state
    project_type = 'test_type'
    initial_exclusions = {'test_exclude1', 'test_exclude2', 'test_exclude3'}
    helper.manager.add_project_type_exclusion(project_type, initial_exclusions)
    
    # Remove some exclusions
    exclusions_to_remove = {'test_exclude1', 'test_exclude2'}
    helper.manager.remove_project_type_exclusion(project_type, exclusions_to_remove)
    
    remaining = helper.manager.project_type_exclusions[project_type]
    assert not exclusions_to_remove.intersection(remaining)
    assert 'test_exclude3' in remaining
    
    helper.check_memory_usage("remove exclusions")

@pytest.mark.timeout(30)
def test_multiple_project_types(helper):
    """Test handling multiple project types"""
    helper.track_memory()
    
    # Setup mixed project structure
    helper.create_project_structure("python")
    helper.create_project_structure("javascript")
    helper.create_project_structure("nextjs")
    
    project_info = {
        'python': True,
        'javascript': True,
        'nextjs': True,
        'web': True
    }
    
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    # Verify combined exclusions
    assert '__pycache__' in exclusions  # Python
    assert 'node_modules' in exclusions  # JavaScript
    assert '.next' in exclusions  # Next.js
    
    helper.check_memory_usage("multiple types")

@pytest.mark.timeout(30)
def test_init_files_handling(helper):
    """Test handling of __init__.py files"""
    helper.track_memory()
    
    # Create nested structure with __init__.py files
    (helper.tmpdir / "package").mkdir()
    (helper.tmpdir / "package" / "__init__.py").touch()
    (helper.tmpdir / "package" / "subpackage").mkdir()
    (helper.tmpdir / "package" / "subpackage" / "__init__.py").touch()
    
    project_info = {'python': True}
    exclusions = helper.manager.get_root_exclusions(project_info, str(helper.tmpdir))
    
    assert '**/__init__.py' in exclusions
    
    helper.check_memory_usage("init files")

@pytest.mark.timeout(30)
def test_get_project_type_exclusions(helper):
    """Test getting exclusions for specific project type"""
    helper.track_memory()
    
    helper.create_project_structure("python")
    
    exclusions = helper.manager._get_project_type_exclusions("python", str(helper.tmpdir))
    
    assert isinstance(exclusions, set)
    assert any('__pycache__' in excl for excl in exclusions)
    
    helper.check_memory_usage("type exclusions")

@pytest.mark.timeout(30)
def test_has_init_files(helper):
    """Test detection of __init__.py files"""
    helper.track_memory()
    
    # Create test structure
    (helper.tmpdir / "package").mkdir()
    (helper.tmpdir / "package" / "__init__.py").touch()
    
    assert helper.manager._has_init_files(str(helper.tmpdir))
    
    helper.check_memory_usage("init detection")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])