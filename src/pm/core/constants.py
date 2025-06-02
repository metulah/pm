# pm/core/constants.py
from pathlib import Path

# Define RESOURCES_DIR centrally in the core layer
# Path(__file__) -> pm/core/constants.py
# .parent -> pm/core/
# .parent -> pm/
# / 'resources' -> pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent / 'resources'

# Add other core constants here if needed
