"""Tests for pm.core.config (Unit Style - With Mocking)

Note on Testing Style:
These tests utilize unittest.mock extensively to isolate the config functions
from the file system and other dependencies (like find_pm_root_path).
This allows for precise testing of logic branches and error handling
(e.g., simulating OSErrors or TomlDecodeErrors) which is difficult
with a purely integration-style approach. While other parts of the test
suite (e.g., CLI, storage) often use direct file system/DB interaction
with temporary resources, the mocking approach was chosen here for more
thorough unit testing of the config module's specific responsibilities.
"""

import pathlib
import toml
from unittest.mock import patch, mock_open


from pm.core import config as sut  # system under test

# --- Constants ---
# find_project_root returns the project root, not the .pm dir itself
MOCK_PROJECT_ROOT_PATH = pathlib.Path("/fake/project")
MOCK_CONFIG_PATH = MOCK_PROJECT_ROOT_PATH / ".pm" / \
    sut.CONFIG_FILENAME  # Expected final path

# --- Tests for get_config_path ---


@patch('pm.core.config.find_project_root')  # Correct patch target
def test_get_config_path_found(mock_find_root):
    """Test get_config_path when .pm root is found (mocked)."""
    # Mock find_project_root to return the *project* root path as a string
    mock_find_root.return_value = str(MOCK_PROJECT_ROOT_PATH)
    # get_config_path should construct the full path correctly
    assert sut.get_config_path() == MOCK_CONFIG_PATH


@patch('pm.core.config.find_project_root')  # Correct patch target
def test_get_config_path_not_found(mock_find_root):
    """Test get_config_path when .pm root is not found (mocked)."""
    mock_find_root.return_value = None
    assert sut.get_config_path() is None

# --- Tests for load_config ---


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.open', new_callable=mock_open, read_data='[section]\nkey = "value"\n[guidelines]\nactive = ["coding"]')
def test_load_config_success(mock_file_open, mock_exists, mock_get_path):
    """Test loading a valid config file (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH  # Mock the final path directly
    mock_exists.return_value = True  # Simulate file exists

    expected_data = {"section": {"key": "value"},
                     "guidelines": {"active": ["coding"]}}
    loaded_data = sut.load_config()

    mock_get_path.assert_called_once()
    mock_exists.assert_called_once()
    mock_file_open.assert_called_once_with("r")
    assert loaded_data == expected_data


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.exists')
def test_load_config_not_exists(mock_exists, mock_get_path):
    """Test loading when config file does not exist (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH
    mock_exists.return_value = False  # Simulate file does not exist

    loaded_data = sut.load_config()

    mock_get_path.assert_called_once()
    mock_exists.assert_called_once()
    assert loaded_data == {}


@patch('pm.core.config.get_config_path')
def test_load_config_no_path(mock_get_path):
    """Test loading when config path cannot be determined (mocked)."""
    mock_get_path.return_value = None  # Simulate path not found

    loaded_data = sut.load_config()

    mock_get_path.assert_called_once()
    assert loaded_data == {}


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.open', new_callable=mock_open, read_data='')  # Empty file
def test_load_config_empty_file(mock_file_open, mock_exists, mock_get_path):
    """Test loading an empty config file (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH
    mock_exists.return_value = True

    loaded_data = sut.load_config()

    mock_file_open.assert_called_once_with("r")
    assert loaded_data == {}


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.open', new_callable=mock_open, read_data='invalid toml {')
@patch('toml.load', side_effect=toml.TomlDecodeError("Mocked decode error", "", 0))
def test_load_config_invalid_toml(mock_toml_load, mock_file_open, mock_exists, mock_get_path):
    """Test loading an invalid TOML file (mocked error)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH
    mock_exists.return_value = True

    loaded_data = sut.load_config()

    mock_file_open.assert_called_once_with("r")
    mock_toml_load.assert_called_once()
    assert loaded_data == {}  # Expect empty dict on decode error


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.open', side_effect=OSError("Mocked permission denied"))
def test_load_config_os_error(mock_file_open_error, mock_exists, mock_get_path):
    """Test loading when an OSError occurs during read (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH
    mock_exists.return_value = True

    loaded_data = sut.load_config()

    mock_file_open_error.assert_called_once_with("r")
    assert loaded_data == {}  # Expect empty dict on OSError

# --- Tests for save_config ---


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.mkdir')
@patch('pathlib.Path.open', new_callable=mock_open)
@patch('toml.dump')
def test_save_config_success(mock_toml_dump, mock_file_open, mock_mkdir, mock_get_path):
    """Test saving a valid config dictionary (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH
    test_data = {"new_section": {"key1": 1, "key2": True}}

    assert sut.save_config(test_data) is True

    mock_get_path.assert_called_once()
    # mkdir called on parent directory (.pm) of the config file
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file_open.assert_called_once_with("w")
    # Check that toml.dump was called with the correct data and file handle
    mock_toml_dump.assert_called_once_with(test_data, mock_file_open())


@patch('pm.core.config.get_config_path')
def test_save_config_no_path(mock_get_path):
    """Test save_config when config path cannot be determined (mocked)."""
    mock_get_path.return_value = None
    assert sut.save_config({"data": "value"}) is False
    mock_get_path.assert_called_once()


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.mkdir')
@patch('pathlib.Path.open', side_effect=OSError("Mocked disk full"))
def test_save_config_os_error_write(mock_file_open_error, mock_mkdir, mock_get_path):
    """Test save_config when an OSError occurs during write (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH

    assert sut.save_config({"data": "value"}) is False

    mock_get_path.assert_called_once()
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file_open_error.assert_called_once_with("w")


@patch('pm.core.config.get_config_path')
@patch('pathlib.Path.mkdir', side_effect=OSError("Mocked permission error"))
def test_save_config_os_error_mkdir(mock_mkdir_error, mock_get_path):
    """Test save_config when an OSError occurs during mkdir (mocked)."""
    mock_get_path.return_value = MOCK_CONFIG_PATH

    assert sut.save_config({"data": "value"}) is False

    mock_get_path.assert_called_once()
    mock_mkdir_error.assert_called_once_with(parents=True, exist_ok=True)


# --- Tests for get_active_guidelines ---

@patch('pm.core.config.load_config')
def test_get_active_guidelines_success(mock_load):
    """Test getting guidelines when section and key exist (mocked load)."""
    mock_load.return_value = {"guidelines": {
        "active": ["coding", "vcs", "123"]}}
    guidelines = sut.get_active_guidelines()
    assert guidelines == ["coding", "vcs", "123"]
    mock_load.assert_called_once()


@patch('pm.core.config.load_config')
def test_get_active_guidelines_missing_active(mock_load):
    """Test getting guidelines when 'active' key is missing (mocked load)."""
    mock_load.return_value = {"guidelines": {"other_key": "value"}}
    guidelines = sut.get_active_guidelines()
    assert guidelines == []
    mock_load.assert_called_once()


@patch('pm.core.config.load_config')
def test_get_active_guidelines_missing_section(mock_load):
    """Test getting guidelines when 'guidelines' section is missing (mocked load)."""
    mock_load.return_value = {"other_section": {"key": "value"}}
    guidelines = sut.get_active_guidelines()
    assert guidelines == []
    mock_load.assert_called_once()


@patch('pm.core.config.load_config')
def test_get_active_guidelines_empty_config(mock_load):
    """Test getting guidelines when config is empty (mocked load)."""
    mock_load.return_value = {}
    guidelines = sut.get_active_guidelines()
    assert guidelines == []
    mock_load.assert_called_once()


@patch('pm.core.config.load_config')
def test_get_active_guidelines_active_not_list(mock_load):
    """Test getting guidelines when 'active' is not a list (mocked load)."""
    mock_load.return_value = {"guidelines": {"active": "not-a-list"}}
    guidelines = sut.get_active_guidelines()
    assert guidelines == []
    mock_load.assert_called_once()


@patch('pm.core.config.load_config')
def test_get_active_guidelines_section_not_dict(mock_load):
    """Test getting guidelines when 'guidelines' is not a dictionary (mocked load)."""
    mock_load.return_value = {"guidelines": ["list", "not", "dict"]}
    guidelines = sut.get_active_guidelines()
    assert guidelines == []
    mock_load.assert_called_once()

# --- Tests for set_active_guidelines ---


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_new_file(mock_save, mock_load):
    """Test setting guidelines when config is initially empty (mocked)."""
    mock_load.return_value = {}  # Simulate empty or non-existent file
    mock_save.return_value = True  # Assume save succeeds
    new_guidelines = ["testing", "docs"]

    assert sut.set_active_guidelines(new_guidelines) is True

    mock_load.assert_called_once()
    # Check that save_config was called with the correctly structured dict
    expected_saved_data = {"guidelines": {"active": ["testing", "docs"]}}
    mock_save.assert_called_once_with(expected_saved_data)


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_existing_file_no_section(mock_save, mock_load):
    """Test setting guidelines when file exists but no [guidelines] section (mocked)."""
    initial_data = {"other": "data"}
    mock_load.return_value = initial_data
    mock_save.return_value = True
    new_guidelines = ["vcs"]

    assert sut.set_active_guidelines(new_guidelines) is True

    mock_load.assert_called_once()
    expected_saved_data = {"other": "data", "guidelines": {"active": ["vcs"]}}
    mock_save.assert_called_once_with(expected_saved_data)


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_existing_file_with_section(mock_save, mock_load):
    """Test setting guidelines overwrites existing 'active' list (mocked)."""
    initial_data = {"guidelines": {
        "active": ["old1", "old2"], "other": "setting"}}
    mock_load.return_value = initial_data
    mock_save.return_value = True
    new_guidelines = ["new1"]

    assert sut.set_active_guidelines(new_guidelines) is True

    mock_load.assert_called_once()
    expected_saved_data = {"guidelines": {
        "active": ["new1"], "other": "setting"}}
    mock_save.assert_called_once_with(expected_saved_data)


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_empty_list(mock_save, mock_load):
    """Test setting an empty list of guidelines (mocked)."""
    initial_data = {"guidelines": {"active": ["old1"]}}
    mock_load.return_value = initial_data
    mock_save.return_value = True
    new_guidelines = []

    assert sut.set_active_guidelines(new_guidelines) is True

    mock_load.assert_called_once()
    expected_saved_data = {"guidelines": {"active": []}}
    mock_save.assert_called_once_with(expected_saved_data)


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_stringifies_input(mock_save, mock_load):
    """Test that input guidelines are stringified before saving (mocked)."""
    mock_load.return_value = {}
    mock_save.return_value = True
    new_guidelines = ["testing", 123, True]  # Mix types

    assert sut.set_active_guidelines(new_guidelines) is True

    mock_load.assert_called_once()
    # Expect strings in the data passed to save_config
    expected_saved_data = {"guidelines": {
        "active": ["testing", "123", "True"]}}
    mock_save.assert_called_once_with(expected_saved_data)


@patch('pm.core.config.load_config')
@patch('pm.core.config.save_config')
def test_set_active_guidelines_save_fails(mock_save, mock_load):
    """Test set_active_guidelines when save_config returns False (mocked)."""
    mock_load.return_value = {}
    mock_save.return_value = False  # Simulate save failure

    assert sut.set_active_guidelines(["any"]) is False

    mock_load.assert_called_once()
    mock_save.assert_called_once()  # save_config should still be called
