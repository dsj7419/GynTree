# tests/unit/test_ProjectTypeDetector.py
import gc
import logging
from pathlib import Path
from typing import Any, Dict, Set

import psutil
import pytest

from services.ProjectTypeDetector import ProjectTypeDetector

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)


class ProjectTypeTestHelper:
    """Helper class for ProjectTypeDetector testing"""

    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None

    def create_project_files(self, project_type: str) -> None:
        """Create test files for specific project type"""
        if project_type == "python":
            (self.tmpdir / "main.py").write_text("print('Hello, World!')")
            (self.tmpdir / "requirements.txt").write_text("pytest\nPyQt5")
            (self.tmpdir / "tests").mkdir(exist_ok=True)

        elif project_type == "javascript":
            (self.tmpdir / "package.json").write_text('{"name": "test"}')
            (self.tmpdir / "index.js").write_text("console.log('hello')")
            (self.tmpdir / "node_modules").mkdir(exist_ok=True)

        elif project_type == "nextjs":
            (self.tmpdir / "next.config.js").write_text("module.exports = {}")
            (self.tmpdir / "pages").mkdir(exist_ok=True)
            (self.tmpdir / "package.json").write_text(
                '{"dependencies": {"next": "^12.0.0"}}'
            )

        elif project_type == "web":
            (self.tmpdir / "index.html").write_text("<html></html>")
            (self.tmpdir / "styles.css").write_text("body {}")

        elif project_type == "database":
            (self.tmpdir / "prisma").mkdir(exist_ok=True)
            (self.tmpdir / "migrations").mkdir(exist_ok=True)
            (self.tmpdir / "schema.prisma").write_text("datasource db {}")

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
                logger.warning(
                    f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB"
                )


@pytest.fixture
def helper(tmpdir):
    """Create test helper instance"""
    return ProjectTypeTestHelper(Path(tmpdir))


@pytest.fixture
def detector(helper):
    """Create ProjectTypeDetector instance"""
    return ProjectTypeDetector(str(helper.tmpdir))


@pytest.mark.timeout(30)
def test_detect_python_project(detector, helper):
    """Test Python project detection"""
    helper.track_memory()

    helper.create_project_files("python")
    assert detector.detect_python_project() is True

    helper.check_memory_usage("python detection")


@pytest.mark.timeout(30)
def test_detect_web_project(detector, helper):
    """Test web project detection"""
    helper.track_memory()

    helper.create_project_files("web")
    assert detector.detect_web_project() is True

    helper.check_memory_usage("web detection")


@pytest.mark.timeout(30)
def test_detect_javascript_project(detector, helper):
    """Test JavaScript project detection"""
    helper.track_memory()

    helper.create_project_files("javascript")
    assert detector.detect_javascript_project() is True

    helper.check_memory_usage("javascript detection")


@pytest.mark.timeout(30)
def test_detect_nextjs_project(detector, helper):
    """Test Next.js project detection"""
    helper.track_memory()

    helper.create_project_files("nextjs")
    assert detector.detect_nextjs_project() is True

    helper.check_memory_usage("nextjs detection")


@pytest.mark.timeout(30)
def test_detect_database_project(detector, helper):
    """Test database project detection"""
    helper.track_memory()

    helper.create_project_files("database")
    assert detector.detect_database_project() is True

    helper.check_memory_usage("database detection")


@pytest.mark.timeout(30)
def test_detect_project_types(detector, helper):
    """Test detection of multiple project types"""
    helper.track_memory()

    helper.create_project_files("python")
    helper.create_project_files("web")
    helper.create_project_files("database")

    detected_types = detector.detect_project_types()
    assert detected_types["python"] is True
    assert detected_types["web"] is True
    assert detected_types["database"] is True
    assert detected_types["javascript"] is False
    assert detected_types["nextjs"] is False

    helper.check_memory_usage("multiple types")


@pytest.mark.timeout(30)
def test_no_project_type_detected(detector, helper):
    """Test behavior when no project type is detected"""
    helper.track_memory()

    detected_types = detector.detect_project_types()
    assert all(value is False for value in detected_types.values())

    helper.check_memory_usage("no types")


@pytest.mark.timeout(30)
def test_multiple_project_types(detector, helper):
    """Test detection of combined project types"""
    helper.track_memory()

    helper.create_project_files("python")
    helper.create_project_files("javascript")
    helper.create_project_files("nextjs")

    detected_types = detector.detect_project_types()
    assert detected_types["python"] is True
    assert detected_types["javascript"] is True
    assert detected_types["nextjs"] is True

    helper.check_memory_usage("combined types")


@pytest.mark.timeout(30)
def test_nested_project_structure(detector, helper):
    """Test detection in nested project structure"""
    helper.track_memory()

    # Create nested structure
    backend = helper.tmpdir / "backend"
    frontend = helper.tmpdir / "frontend"
    backend.mkdir()
    frontend.mkdir()

    (backend / "main.py").write_text("print('Hello, World!')")
    (frontend / "package.json").write_text("{}")

    detected_types = detector.detect_project_types()
    assert detected_types["python"] is True
    assert detected_types["javascript"] is True

    helper.check_memory_usage("nested structure")


@pytest.mark.timeout(30)
def test_empty_directory(detector, helper):
    """Test detection in empty directory"""
    helper.track_memory()

    detected_types = detector.detect_project_types()
    assert all(value is False for value in detected_types.values())

    helper.check_memory_usage("empty directory")


@pytest.mark.timeout(30)
def test_only_config_files(detector, helper):
    """Test detection with only config files"""
    helper.track_memory()

    (helper.tmpdir / ".gitignore").write_text("node_modules")
    (helper.tmpdir / "README.md").write_text("# Project README")

    detected_types = detector.detect_project_types()
    assert all(value is False for value in detected_types.values())

    helper.check_memory_usage("config files")


@pytest.mark.timeout(30)
def test_mixed_project_indicators(detector, helper):
    """Test detection with mixed project indicators"""
    helper.track_memory()

    # Create mixed indicators
    (helper.tmpdir / "main.py").write_text("print('Hello')")
    (helper.tmpdir / "index.html").write_text("<html></html>")
    (helper.tmpdir / "schema.prisma").write_text("model User {}")
    (helper.tmpdir / "next.config.js").write_text("module.exports = {}")
    (helper.tmpdir / "pages").mkdir()

    detected_types = detector.detect_project_types()

    # Verify correct type detection
    assert detected_types["python"] is True
    assert detected_types["web"] is True
    assert detected_types["nextjs"] is True
    assert detected_types["database"] is True

    helper.check_memory_usage("mixed indicators")


@pytest.mark.timeout(30)
def test_partial_project_structure(detector, helper):
    """Test detection with partial project structure"""
    helper.track_memory()

    # Create partial structures
    (helper.tmpdir / "pages").mkdir()  # Next.js directory but no config
    (helper.tmpdir / "node_modules").mkdir()  # Node modules but no package.json

    detected_types = detector.detect_project_types()

    # Verify correct handling of partial structures
    assert detected_types["nextjs"] is False
    assert detected_types["javascript"] is False

    helper.check_memory_usage("partial structure")


@pytest.mark.timeout(30)
def test_case_sensitivity(detector, helper):
    """Test case sensitivity in detection"""
    helper.track_memory()

    # Create files with different cases
    (helper.tmpdir / "MAIN.py").write_text("print('Hello')")
    (helper.tmpdir / "Package.JSON").write_text("{}")

    detected_types = detector.detect_project_types()
    assert detected_types["python"] is True
    assert detected_types["javascript"] is True

    helper.check_memory_usage("case sensitivity")


@pytest.mark.timeout(30)
def test_memory_efficiency(detector, helper):
    """Test memory efficiency with large project structure"""
    helper.track_memory()

    # Create large project structure
    for i in range(1000):
        (helper.tmpdir / f"module_{i}").mkdir()
        (helper.tmpdir / f"module_{i}" / "main.py").write_text(f"# Module {i}")
        (helper.tmpdir / f"module_{i}" / "package.json").write_text("{}")

    detected_types = detector.detect_project_types()
    assert detected_types["python"] is True
    assert detected_types["javascript"] is True

    current_memory = psutil.Process().memory_info().rss
    memory_diff = current_memory - helper.initial_memory
    assert memory_diff < 50 * 1024 * 1024  # Less than 50MB increase

    helper.check_memory_usage("large structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
