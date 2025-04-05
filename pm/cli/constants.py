# pm/cli/constants.py
from pathlib import Path

# Define RESOURCES_DIR centrally here
# Path(__file__) -> pm/cli/constants.py
# .parent -> pm/cli/
# .parent -> pm/
# / 'resources' -> pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent / 'resources'

# Add other shared constants here if needed in the future
