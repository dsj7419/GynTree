import pytest
from services.ProjectTypeDetector import ProjectTypeDetector

@pytest.fixture
def detector(tmpdir):
    return ProjectTypeDetector(str(tmpdir))

def test_detect_python_project(detector, tmpdir):
    tmpdir.join("main.py").write("print('Hello, world!')")
    assert detector.detect_python_project() == True

def test_detect_web_project(detector, tmpdir):
    tmpdir.join("index.html").write("<html></html>")
    assert detector.detect_web_project() == True

def test_detect_javascript_project(detector, tmpdir):
    tmpdir.join("package.json").write("{}")
    assert detector.detect_javascript_project() == True

def test_detect_nextjs_project(detector, tmpdir):
    tmpdir.join("next.config.js").write("module.exports = {}")
    tmpdir.mkdir("pages")
    assert detector.detect_nextjs_project() == True

def test_detect_database_project(detector, tmpdir):
    tmpdir.mkdir("migrations")
    assert detector.detect_database_project() == True

def test_detect_project_types(detector, tmpdir):
    tmpdir.join("main.py").write("print('Hello, world!')")
    tmpdir.join("index.html").write("<html></html>")
    tmpdir.mkdir("migrations")
    detected_types = detector.detect_project_types()
    assert detected_types['python'] == True
    assert detected_types['web'] == True
    assert detected_types['database'] == True
    assert detected_types['javascript'] == False
    assert detected_types['nextjs'] == False

def test_no_project_type_detected(detector, tmpdir):
    detected_types = detector.detect_project_types()
    assert all(value == False for value in detected_types.values())

def test_multiple_project_types(detector, tmpdir):
    tmpdir.join("main.py").write("print('Hello, world!')")
    tmpdir.join("package.json").write("{}")
    tmpdir.join("next.config.js").write("module.exports = {}")
    tmpdir.mkdir("pages")
    detected_types = detector.detect_project_types()
    assert detected_types['python'] == True
    assert detected_types['javascript'] == True
    assert detected_types['nextjs'] == True

def test_nested_project_structure(detector, tmpdir):
    backend = tmpdir.mkdir("backend")
    backend.join("main.py").write("print('Hello, world!')")
    frontend = tmpdir.mkdir("frontend")
    frontend.join("package.json").write("{}")
    detected_types = detector.detect_project_types()
    assert detected_types['python'] == True
    assert detected_types['javascript'] == True

def test_empty_directory(detector, tmpdir):
    detected_types = detector.detect_project_types()
    assert all(value == False for value in detected_types.values())

def test_only_config_files(detector, tmpdir):
    tmpdir.join(".gitignore").write("node_modules")
    tmpdir.join("README.md").write("# Project README")
    detected_types = detector.detect_project_types()
    assert all(value == False for value in detected_types.values())