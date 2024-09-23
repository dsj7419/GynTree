import pytest
from services.ProjectTypeDetector import ProjectTypeDetector

pytestmark = pytest.mark.unit

@pytest.fixture
def detector(tmpdir):
    return ProjectTypeDetector(str(tmpdir))

def test_detect_python_project(detector, tmpdir):
    tmpdir.join("main.py").write("print('Hello, World!')")
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
    tmpdir.join("main.py").write("print('Hello, World!')")
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
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("package.json").write("{}")
    tmpdir.join("next.config.js").write("module.exports = {}")
    tmpdir.mkdir("pages")
    detected_types = detector.detect_project_types()
    assert detected_types['python'] == True
    assert detected_types['javascript'] == True
    assert detected_types['nextjs'] == True

def test_nested_project_structure(detector, tmpdir):
    backend = tmpdir.mkdir("backend")
    backend.join("main.py").write("print('Hello, World!')")
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

''' def test_detect_react_project(detector, tmpdir):
    tmpdir.join("package.json").write('{"dependencies": {"react": "^17.0.2"}}')
    assert detector.detect_react_project() == True

def test_detect_vue_project(detector, tmpdir):
    tmpdir.join("package.json").write('{"dependencies": {"vue": "^3.0.0"}}')
    assert detector.detect_vue_project() == True

def test_detect_angular_project(detector, tmpdir):
    tmpdir.join("angular.json").write("{}")
    assert detector.detect_angular_project() == True

def test_detect_django_project(detector, tmpdir):
    tmpdir.join("manage.py").write("#!/usr/bin/env python")
    assert detector.detect_django_project() == True

def test_detect_flask_project(detector, tmpdir):
    tmpdir.join("app.py").write("from flask import Flask")
    assert detector.detect_flask_project() == True

def test_detect_ruby_on_rails_project(detector, tmpdir):
    tmpdir.mkdir("app")
    tmpdir.mkdir("config")
    tmpdir.join("Gemfile").write("source 'https://rubygems.org'")
    assert detector.detect_ruby_on_rails_project() == True

def test_detect_laravel_project(detector, tmpdir):
    tmpdir.join("artisan").write("#!/usr/bin/env php")
    assert detector.detect_laravel_project() == True

def test_detect_spring_boot_project(detector, tmpdir):
    tmpdir.join("pom.xml").write("<groupId>org.springframework.boot</groupId>")
    assert detector.detect_spring_boot_project() == True

def test_detect_dotnet_project(detector, tmpdir):
    tmpdir.join("Program.cs").write("using System;")
    assert detector.detect_dotnet_project() == True '''