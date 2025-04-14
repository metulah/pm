"""Tests for pm.cli.guideline.utils"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock  # Import MagicMock

# Import the function to test and any constants needed
from pm.cli.guideline.utils import discover_available_guidelines
# No need to import cli_constants directly if we mock RESOURCES_DIR

# --- Fixtures ---


@pytest.fixture
def mock_resources_dir(tmp_path):
    """Creates a temporary directory to mock pm/resources."""
    res_dir = tmp_path / "mock_resources"
    res_dir.mkdir()
    return res_dir

# --- Helper to create mock Path objects for iterdir ---


def create_mock_path(name: str, is_file: bool, content: str = "", path_obj=None):
    mock = MagicMock(spec=Path)
    mock.name = name
    mock.is_file.return_value = is_file
    mock.is_dir.return_value = not is_file
    # Store the actual Path object if provided (for assertions)
    # Use the provided path_obj or construct one based on name for comparison
    mock.actual_path = path_obj if path_obj else Path(name)
    # If it's a file, mock read_text
    if is_file:
        mock.read_text.return_value = content
    return mock

# --- Tests for discover_available_guidelines ---

# Patch the RESOURCES_DIR constant within the utils module


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
def test_discover_no_files(mock_res_dir_path, mock_resources_dir):
    """Test discovery when the resources directory is empty."""
    # Configure the mock RESOURCES_DIR Path object
    mock_res_dir_path.is_dir.return_value = True
    mock_res_dir_path.iterdir.return_value = []  # Simulate empty directory

    result = discover_available_guidelines()
    assert result == []
    mock_res_dir_path.is_dir.assert_called_once()
    mock_res_dir_path.iterdir.assert_called_once()


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
def test_discover_non_matching_files(mock_res_dir_path, mock_resources_dir):
    """Test discovery ignores files that don't match the pattern."""
    mock_res_dir_path.is_dir.return_value = True

    # Create mock Path objects for iterdir results
    mock_file1 = create_mock_path("readme.txt", is_file=True)
    mock_file2 = create_mock_path(
        "welcome_guidelines.md", is_file=True)  # Missing slug
    mock_file3 = create_mock_path("other_file_coding.md", is_file=True)
    mock_dir = create_mock_path("subdir", is_file=False)

    mock_res_dir_path.iterdir.return_value = [
        mock_file1, mock_file2, mock_dir, mock_file3]

    result = discover_available_guidelines()
    assert result == []
    mock_res_dir_path.is_dir.assert_called_once()
    mock_res_dir_path.iterdir.assert_called_once()


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
@patch('pm.cli.guideline.utils.frontmatter.load')  # Mock frontmatter loading
def test_discover_matching_files_no_frontmatter(mock_fm_load, mock_res_dir_path, mock_resources_dir):
    """Test discovery finds files and uses slug for title if no frontmatter."""
    mock_res_dir_path.is_dir.return_value = True

    # Simulate frontmatter.load raising an exception or returning non-dict metadata
    mock_fm_load.side_effect = Exception("Mocked load error")

    # Create mock Path objects for iterdir results
    # Store the real path for assertion comparison
    file1_real_path = mock_resources_dir / "welcome_guidelines_coding.md"
    mock_file1 = create_mock_path(
        "welcome_guidelines_coding.md", is_file=True, path_obj=file1_real_path)

    file2_real_path = mock_resources_dir / "welcome_guidelines_vcs_usage.md"
    mock_file2 = create_mock_path(
        "welcome_guidelines_vcs_usage.md", is_file=True, path_obj=file2_real_path)

    mock_res_dir_path.iterdir.return_value = [mock_file1, mock_file2]

    result = discover_available_guidelines()

    assert len(result) == 2
    # Results should be sorted by slug
    # FIX: Compare against mock_file1.actual_path
    assert result[0] == {
        "slug": "coding",
        "path": mock_file1.actual_path,  # Use the stored actual path
        "title": "Coding",  # Default title from slug
        "description": None
    }
    # FIX: Compare against mock_file2.actual_path
    assert result[1] == {
        "slug": "vcs_usage",
        "path": mock_file2.actual_path,  # Use the stored actual path
        "title": "Vcs Usage",  # Default title from slug
        "description": None
    }
    assert mock_fm_load.call_count == 2  # Ensure frontmatter.load was attempted


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
@patch('pm.cli.guideline.utils.frontmatter.load')  # Mock frontmatter loading
def test_discover_files_with_frontmatter(mock_fm_load, mock_res_dir_path, mock_resources_dir):
    """Test discovery reads title and description from frontmatter."""
    mock_res_dir_path.is_dir.return_value = True

    # --- Mock frontmatter.load results ---
    # Mock Post object structure expected by the code
    mock_post1 = MagicMock()
    mock_post1.metadata = {"title": " Custom Coding Title ",
                           "description": " How we write code. "}  # With extra spaces

    mock_post2 = MagicMock()
    mock_post2.metadata = {"title": "Version Control"}  # No description

    mock_post3 = MagicMock()
    mock_post3.metadata = {
        "description": "Testing procedures."}  # Only description

    # Configure side_effect based on the path passed to frontmatter.load
    def fm_load_side_effect(path_arg):
        # Compare using the 'actual_path' stored on the mock
        if path_arg.actual_path.name == "welcome_guidelines_coding.md":
            return mock_post1
        elif path_arg.actual_path.name == "welcome_guidelines_vcs.md":
            return mock_post2
        elif path_arg.actual_path.name == "welcome_guidelines_testing.md":
            return mock_post3
        else:
            raise Exception(
                f"Unexpected file passed to mock frontmatter.load: {path_arg.actual_path.name}")
    mock_fm_load.side_effect = fm_load_side_effect
    # --- End Mock frontmatter.load results ---

    # Create mock Path objects for iterdir results
    file1_real_path = mock_resources_dir / "welcome_guidelines_coding.md"
    mock_file1 = create_mock_path(
        "welcome_guidelines_coding.md", is_file=True, path_obj=file1_real_path)

    file2_real_path = mock_resources_dir / "welcome_guidelines_vcs.md"
    mock_file2 = create_mock_path(
        "welcome_guidelines_vcs.md", is_file=True, path_obj=file2_real_path)

    file3_real_path = mock_resources_dir / "welcome_guidelines_testing.md"
    mock_file3 = create_mock_path(
        "welcome_guidelines_testing.md", is_file=True, path_obj=file3_real_path)

    mock_res_dir_path.iterdir.return_value = [
        mock_file1, mock_file2, mock_file3]  # Order doesn't matter here

    result = discover_available_guidelines()

    assert len(result) == 3
    # Results sorted by slug: coding, testing, vcs
    # FIX: Compare against mock_fileX.actual_path
    assert result[0] == {
        "slug": "coding",
        "path": mock_file1.actual_path,
        "title": "Custom Coding Title",  # From frontmatter, stripped
        "description": "How we write code."  # From frontmatter, stripped
    }
    assert result[1] == {
        "slug": "testing",
        "path": mock_file3.actual_path,
        "title": "Testing",  # Default title from slug (no title in fm)
        "description": "Testing procedures."  # From frontmatter
    }
    assert result[2] == {
        "slug": "vcs",
        "path": mock_file2.actual_path,
        "title": "Version Control",  # From frontmatter
        "description": None  # No description in frontmatter
    }
    assert mock_fm_load.call_count == 3


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
@patch('pm.cli.guideline.utils.frontmatter.load')  # Mock frontmatter loading
def test_discover_invalid_frontmatter(mock_fm_load, mock_res_dir_path, mock_resources_dir):
    """Test discovery handles invalid frontmatter gracefully, using defaults."""
    mock_res_dir_path.is_dir.return_value = True

    # --- Mock frontmatter.load results ---
    mock_post_valid = MagicMock()
    mock_post_valid.metadata = {"title": "Valid"}

    def fm_load_side_effect(path_arg):
        # Compare using the 'actual_path' stored on the mock
        if path_arg.actual_path.name == "welcome_guidelines_valid.md":
            return mock_post_valid
        elif path_arg.actual_path.name == "welcome_guidelines_invalid.md":
            # Simulate error
            raise Exception("Simulated frontmatter parsing error")
        else:
            raise Exception(
                f"Unexpected file passed to mock frontmatter.load: {path_arg.actual_path.name}")
    mock_fm_load.side_effect = fm_load_side_effect
    # --- End Mock frontmatter.load results ---

    # Create mock Path objects for iterdir results
    file1_real_path = mock_resources_dir / "welcome_guidelines_valid.md"
    mock_file1 = create_mock_path(
        "welcome_guidelines_valid.md", is_file=True, path_obj=file1_real_path)

    file2_real_path = mock_resources_dir / "welcome_guidelines_invalid.md"
    mock_file2 = create_mock_path(
        "welcome_guidelines_invalid.md", is_file=True, path_obj=file2_real_path)

    mock_res_dir_path.iterdir.return_value = [mock_file1, mock_file2]

    result = discover_available_guidelines()

    assert len(result) == 2
    # Results sorted by slug: invalid, valid
    # FIX: Compare against mock_fileX.actual_path
    assert result[0] == {
        "slug": "invalid",
        "path": mock_file2.actual_path,
        "title": "Invalid",  # Default title from slug
        "description": None
    }
    assert result[1] == {
        "slug": "valid",
        "path": mock_file1.actual_path,
        "title": "Valid",  # From frontmatter
        "description": None
    }
    assert mock_fm_load.call_count == 2


@patch('pm.cli.guideline.utils.RESOURCES_DIR')
def test_discover_resources_dir_not_found(mock_res_dir_path):
    """Test discovery when the resources directory itself doesn't exist."""
    # Configure the mock RESOURCES_DIR Path object
    mock_res_dir_path.is_dir.return_value = False  # Simulate it's not a dir

    result = discover_available_guidelines()
    assert result == []
    mock_res_dir_path.is_dir.assert_called_once()
    # Should not iterate if dir doesn't exist
    mock_res_dir_path.iterdir.assert_not_called()
