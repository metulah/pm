import pytest
import uuid
from datetime import datetime
from click.testing import CliRunner

from pm.storage import init_db


@pytest.fixture(scope="function")
def cli_runner_env(tmp_path):
    """Provides a CliRunner and an initialized temporary DB path for CLI note tests."""
    db_path = str(tmp_path / "test_cli_note.db")
    conn = init_db(db_path)
    # Create a dummy project and task for CLI tests
    project_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    project_slug = "cli-note-proj"
    task_slug = "cli-note-task"
    with conn:
        conn.execute(
            "INSERT INTO projects (id, name, slug, created_at, updated_at, status) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, "CLINoteProject", project_slug,
             datetime.now(), datetime.now(), "ACTIVE")
        )
        conn.execute(
            "INSERT INTO tasks (id, project_id, name, slug, created_at, updated_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, project_id, "CLINoteTask", task_slug,
             datetime.now(), datetime.now(), "NOT_STARTED")
        )
    conn.close()
    runner = CliRunner(mix_stderr=False)
    # Return runner, db_path, and identifiers for use in tests
    return runner, db_path, {"project_id": project_id, "project_slug": project_slug, "task_id": task_id, "task_slug": task_slug}
