import os

import pytest

from services.auto_exclude.IDEandGitAutoExclude import IDEandGitAutoExclude
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_project_type_detector(mocker):
    return mocker.Mock(spec=ProjectTypeDetector)


@pytest.fixture
def mock_settings_manager(mocker):
    manager = mocker.Mock(spec=SettingsManager)
    manager.is_excluded.return_value = False
    return manager


@pytest.fixture
def ide_git_exclude(tmpdir, mock_project_type_detector, mock_settings_manager):
    return IDEandGitAutoExclude(
        str(tmpdir), mock_project_type_detector, mock_settings_manager
    )


@pytest.mark.timeout(30)
def test_get_exclusions_common_patterns(ide_git_exclude):
    """Test common IDE and Git exclusions are included"""
    exclusions = ide_git_exclude.get_exclusions()

    # Check root exclusions
    expected_root = {".git", ".vs", ".idea", ".vscode"}
    assert expected_root.issubset(exclusions["root_exclusions"])

    # Check file exclusions
    expected_files = {
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".dockerignore",
        "Thumbs.db",
        ".DS_Store",
        "*.swp",
        "*~",
    }
    assert expected_files.issubset(exclusions["excluded_files"])


@pytest.mark.timeout(30)
def test_get_exclusions_with_existing_files(ide_git_exclude, tmpdir):
    """Test exclusions with actual files present"""
    # Create test files
    ide_files = [".gitignore", ".vsignore", ".editorconfig"]
    for file in ide_files:
        tmpdir.join(file).write("test content")

    exclusions = ide_git_exclude.get_exclusions()

    for file in ide_files:
        assert (
            os.path.relpath(
                os.path.join(str(tmpdir), file), ide_git_exclude.start_directory
            )
            in exclusions["excluded_files"]
        )


@pytest.mark.timeout(30)
def test_temp_file_patterns(ide_git_exclude, tmpdir):
    """Test temporary file exclusion patterns"""
    test_files = ["test.tmp", "backup.bak", "~file", ".file.swp"]

    for file in test_files:
        tmpdir.join(file).write("test content")

    exclusions = ide_git_exclude.get_exclusions()

    for file in test_files:
        relative_path = os.path.relpath(
            os.path.join(str(tmpdir), file), ide_git_exclude.start_directory
        )
        assert any(
            pattern in exclusions["excluded_files"]
            for pattern in ["*.tmp", "*.bak", "*~", "*.swp"]
        )


@pytest.mark.timeout(30)
def test_nested_ide_directories(ide_git_exclude, tmpdir):
    """Test handling of nested IDE directories"""
    os.makedirs(os.path.join(str(tmpdir), "project1", ".git"))
    os.makedirs(os.path.join(str(tmpdir), "project1", "subproject", ".git"))

    exclusions = ide_git_exclude.get_exclusions()
    assert ".git" in exclusions["root_exclusions"]


@pytest.mark.timeout(30)
def test_combined_patterns(ide_git_exclude, tmpdir):
    """Test handling of multiple exclusion patterns together"""
    # Create mixed test structure
    os.makedirs(os.path.join(str(tmpdir), ".git"))
    os.makedirs(os.path.join(str(tmpdir), ".vscode"))
    tmpdir.join(".gitignore").write("")
    tmpdir.join("file.tmp").write("")

    exclusions = ide_git_exclude.get_exclusions()

    # Verify combined patterns
    assert ".git" in exclusions["root_exclusions"]
    assert ".vscode" in exclusions["root_exclusions"]
    assert ".gitignore" in str(exclusions["excluded_files"])
    assert "*.tmp" in str(exclusions["excluded_files"])
