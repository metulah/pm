# tests/cli/welcome/conftest.py
import pytest
from click.testing import CliRunner
from pathlib import Path

# Define expected content snippets (adjust if actual content changes)
# Assuming these files exist in pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent.parent.parent / \
    'pm' / 'resources'  # Go up levels from tests/cli/welcome
DEFAULT_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_pm.md'
CODING_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_coding.md'
VCS_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_vcs.md'
TESTING_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_testing.md'

# Read actual snippets to make tests less brittle to minor wording changes
# Use more unique snippets if possible
DEFAULT_CONTENT_SNIPPET = "Session Workflow"  # Snippet from the 'pm' guideline
# Define snippets for new guidelines
CODING_CONTENT_SNIPPET = "Follow the project's coding standards"  # Fallback
VCS_CONTENT_SNIPPET = "Commit changes frequently"  # Fallback
TESTING_CONTENT_SNIPPET = "Write and/or update tests"  # Fallback
try:
    # Update snippet reading logic for the 'pm' guideline if needed
    if DEFAULT_GUIDELINE_PATH.is_file():
        pm_lines = DEFAULT_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()
        # Example: Use a snippet known to be in pm guideline
        if any('Session Workflow' in line for line in pm_lines):
            DEFAULT_CONTENT_SNIPPET = "Session Workflow"
        # Add other potential stable snippets if needed
        # else: keep the original fallback defined above
    if CODING_GUIDELINE_PATH.is_file():
        # Get the core text of the last line
        last_line = CODING_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()[-1].strip()
        if last_line.startswith('• '):
            CODING_CONTENT_SNIPPET = last_line[2:]  # Remove bullet and space
        elif last_line.startswith('- '):
            CODING_CONTENT_SNIPPET = last_line[2:]  # Remove dash and space
        else:
            CODING_CONTENT_SNIPPET = last_line
    if VCS_GUIDELINE_PATH.is_file():
        # Use a different snippet (line 12) that might be more stable after rendering
        vcs_lines = VCS_GUIDELINE_PATH.read_text(encoding='utf-8').splitlines()
        if len(vcs_lines) > 11 and 'Commit Changes Frequently:' in vcs_lines[11]:
            VCS_CONTENT_SNIPPET = "Commit Changes Frequently:"
        # else: keep fallback
    if TESTING_GUIDELINE_PATH.is_file():
        # Get the first bullet point (line index 2)
        testing_lines = TESTING_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()
        if len(testing_lines) > 2:
            # Use line index 6 for a more specific snippet
            line_content = testing_lines[6].strip()
            if line_content.startswith('• '):
                # Remove bullet and space
                TESTING_CONTENT_SNIPPET = line_content[2:]
            elif line_content.startswith('- '):
                # Remove dash and space
                TESTING_CONTENT_SNIPPET = line_content[2:]
            else:
                TESTING_CONTENT_SNIPPET = line_content
except Exception:
    print("Warning: Could not read guideline files for test snippets. Using fallbacks.")
    pass  # Keep fallback if reading fails during test setup

CUSTOM_FILE_CONTENT = "This is a custom guideline from a test file."
SEPARATOR = "\n\n<<<--- GUIDELINE SEPARATOR --->>>\n\n"  # Define a unique separator


@pytest.fixture(scope="module")
def runner():
    """Provides a Click CliRunner with separated stderr."""
    # mix_stderr=False is important to capture stderr separately for warnings
    return CliRunner(mix_stderr=False)


@pytest.fixture(scope="function")
def temp_guideline_file(tmp_path):
    """Creates a temporary guideline file for testing @path."""
    file_path = tmp_path / "custom_guidelines.md"
    file_path.write_text(CUSTOM_FILE_CONTENT, encoding='utf-8')
    yield file_path  # Use yield to ensure cleanup if needed, though tmp_path handles it


@pytest.fixture(scope="function")
def temp_pm_dir(tmp_path: Path) -> Path:
    """Creates a .pm directory within the tmp_path for config testing."""
    pm_dir = tmp_path / ".pm"
    pm_dir.mkdir(exist_ok=True)
    return pm_dir
