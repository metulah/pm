# tests/core/test_core_guideline.py
import pytest
import frontmatter
from pathlib import Path
from unittest.mock import patch

# Function to test
from pm.core.guideline import get_available_guidelines

# Helper to create mock guideline files


def create_mock_file(path: Path, content: str, metadata: dict = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(content=content, metadata=metadata or {})
    path.write_text(frontmatter.dumps(post), encoding='utf-8')


@pytest.fixture
def mock_dirs(tmp_path):
    """Fixture to create temporary directories for testing."""
    mock_resources_dir = tmp_path / "mock_resources"
    mock_project_root = tmp_path / "mock_project"
    mock_pm_dir = mock_project_root / ".pm"
    mock_custom_guidelines_dir = mock_pm_dir / "guidelines"

    # Create directories
    mock_resources_dir.mkdir()
    mock_project_root.mkdir()
    # Custom dir might not always exist, don't create it by default here

    return {
        "resources": mock_resources_dir,
        "project_root": mock_project_root,
        "custom": mock_custom_guidelines_dir
    }

# --- Test Cases ---


def test_get_available_guidelines_only_builtin(mock_dirs):
    """Test discovering only built-in guidelines."""
    # Create mock built-in files
    create_mock_file(
        mock_dirs["resources"] / "welcome_guidelines_coding.md",
        "Coding content",
        {"title": "Coding Standards", "description": "Best practices for code."}
    )
    create_mock_file(
        mock_dirs["resources"] / "welcome_guidelines_vcs.md",
        "VCS content",
        {"description": "Version control usage."}  # No title, should default
    )

    # Patch RESOURCES_DIR and find_project_root (to return None, no custom dir)
    with patch('pm.core.guideline.RESOURCES_DIR', mock_dirs["resources"]), \
            patch('pm.core.guideline.find_project_root', return_value=None):
        guidelines = get_available_guidelines()

    assert len(guidelines) == 2
    assert guidelines[0]['slug'] == 'coding'
    assert guidelines[0]['type'] == 'Built-in'
    assert guidelines[0]['title'] == 'Coding Standards'
    assert guidelines[0]['description'] == 'Best practices for code.'
    assert guidelines[1]['slug'] == 'vcs'
    assert guidelines[1]['type'] == 'Built-in'
    assert guidelines[1]['title'] == 'Vcs'  # Default title from slug
    assert guidelines[1]['description'] == 'Version control usage.'


def test_get_available_guidelines_only_custom(mock_dirs):
    """Test discovering only custom guidelines."""
    # Create mock custom files
    # Ensure custom dir exists
    mock_dirs["custom"].mkdir(parents=True, exist_ok=True)
    create_mock_file(
        mock_dirs["custom"] / "testing.md",
        "Testing content",
        {"title": "Testing Strategy", "description": "How we test."}
    )

    # Patch RESOURCES_DIR (empty) and find_project_root
    with patch('pm.core.guideline.RESOURCES_DIR', mock_dirs["resources"]), \
            patch('pm.core.guideline.find_project_root', return_value=mock_dirs["project_root"]):
        guidelines = get_available_guidelines()

    assert len(guidelines) == 1
    assert guidelines[0]['slug'] == 'testing'
    assert guidelines[0]['type'] == 'Custom'
    assert guidelines[0]['title'] == 'Testing Strategy'
    assert guidelines[0]['description'] == 'How we test.'


def test_get_available_guidelines_override(mock_dirs):
    """Test custom guidelines overriding built-in ones."""
    # Create mock built-in file
    create_mock_file(
        mock_dirs["resources"] / "welcome_guidelines_coding.md",
        "Built-in coding content",
        {"title": "Built-in Coding", "description": "Old coding rules."}
    )
    # Create mock custom file with the same slug
    mock_dirs["custom"].mkdir(parents=True, exist_ok=True)
    create_mock_file(
        mock_dirs["custom"] / "coding.md",
        "Custom coding content",
        {"title": "Custom Coding Rules", "description": "New coding rules!"}
    )
    # Create another built-in for good measure
    create_mock_file(
        mock_dirs["resources"] / "welcome_guidelines_vcs.md",
        "VCS content",
        {"description": "Version control usage."}
    )

    # Patch RESOURCES_DIR and find_project_root
    with patch('pm.core.guideline.RESOURCES_DIR', mock_dirs["resources"]), \
            patch('pm.core.guideline.find_project_root', return_value=mock_dirs["project_root"]):
        guidelines = get_available_guidelines()

    # Should have custom 'coding' and built-in 'vcs'
    assert len(guidelines) == 2
    # Check sorting and content
    assert guidelines[0]['slug'] == 'coding'
    assert guidelines[0]['type'] == 'Custom'
    assert guidelines[0]['title'] == 'Custom Coding Rules'
    assert guidelines[0]['description'] == 'New coding rules!'
    assert guidelines[1]['slug'] == 'vcs'
    assert guidelines[1]['type'] == 'Built-in'
    assert guidelines[1]['title'] == 'Vcs'
    assert guidelines[1]['description'] == 'Version control usage.'


def test_get_available_guidelines_no_guidelines(mock_dirs):
    """Test when no guidelines are found."""
    # Patch RESOURCES_DIR (empty) and find_project_root (no custom dir)
    with patch('pm.core.guideline.RESOURCES_DIR', mock_dirs["resources"]), \
            patch('pm.core.guideline.find_project_root', return_value=mock_dirs["project_root"]):
        # Note: mock_dirs["custom"] was not created in this test setup
        guidelines = get_available_guidelines()

    assert len(guidelines) == 0


def test_get_available_guidelines_resources_dir_missing(mock_dirs, capsys):
    """Test when the built-in resources directory doesn't exist."""
    mock_dirs["resources"].rmdir()  # Remove the mock resources dir

    # Patch RESOURCES_DIR (now points to non-existent path) and find_project_root
    with patch('pm.core.guideline.RESOURCES_DIR', mock_dirs["resources"]), \
            patch('pm.core.guideline.find_project_root', return_value=None):
        guidelines = get_available_guidelines()

    assert len(guidelines) == 0
    captured = capsys.readouterr()
    # Check if the warning was printed (adjust if logging is implemented)
    assert f"[Warning] Built-in resources directory not found: {mock_dirs['resources']}" in captured.out

# TODO: Add tests for malformed frontmatter, project_root not found affecting custom scan, etc.
