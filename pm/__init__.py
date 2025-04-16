# Project management package initialization
__version__ = "0.1.0"

# Re-exports from submodules (moved from pm/pm/__init__.py)
from .cli import cli
from .models import Project, Task
from .storage import init_db

__all__ = ["cli", "Project", "Task", "init_db", "__version__"]
