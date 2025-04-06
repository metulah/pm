"""
Original tests for task CLI commands.

NOTE: Tests from this file have been refactored into more specific files:
- tests/test_cli_task_crud.py
- tests/test_cli_task_description.py
- tests/test_cli_task_delete.py
- tests/test_cli_task_status.py
- tests/test_cli_task_dependency.py

This file is kept temporarily for history but contains no active tests.
Consider removing it in the future if desired.
"""

import pytest
import json
import sqlite3
import os
from pathlib import Path
from pm.storage import init_db, get_task
from pm.cli.common_utils import get_db_connection  # Import from common_utils
from pm.core.types import TaskStatus
from pm.cli.__main__ import cli
from click.testing import CliRunner
from pm.storage.task import get_task_dependencies

# --- Fixture for CLI Runner and DB Path (kept for potential future use/consistency) ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    conn.close()
    runner = CliRunner(mix_stderr=False)
    return runner, db_path

# No tests remain in this file.
