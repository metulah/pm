"""Tests for CLI command workflows related to deletion."""

import pytest
import json
from pm.storage import init_db
from pm.cli import cli
from click.testing import CliRunner

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    return runner, db_path

# --- Deletion Workflow Tests ---


def test_cli_project_delete_standard(cli_runner_env):
    """Test standard project deletion logic (fail with task, success empty) using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Delete Test Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Task In Delete Project'])  # Use slug
    task_data = json.loads(result_task.output)['data']
    task_slug = task_data['slug']

    # Test deleting project (using slug) with task (should fail because --force is missing)
    result_del_fail = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_slug])
    # Expect non-zero exit code because --force is missing
    assert result_del_fail.exit_code != 0
    # Check stderr for the specific error message
    assert "Error: Deleting a project is irreversible" in result_del_fail.stderr
    assert "--force" in result_del_fail.stderr

    # Test deleting the task (using project slug and task slug) - requires --force
    result_del_task = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete', project_slug, task_slug, '--force'])
    assert result_del_task.exit_code == 0
    assert json.loads(result_del_task.output)["status"] == "success"

    # Test deleting project (using slug) without task (should succeed with --force)
    result_del_ok = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'delete', project_slug, '--force'])
    assert result_del_ok.exit_code == 0
    response_del_ok = json.loads(result_del_ok.output)
    assert response_del_ok["status"] == "success"
    assert "deleted" in response_del_ok["message"]

    # Verify project is gone (using slug)
    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_slug])
    assert result_show.exit_code == 0  # Command runs but returns error status
    assert json.loads(result_show.output)["status"] == "error"
    assert "not found" in json.loads(result_show.output)["message"]


def test_cli_project_delete_force(cli_runner_env):
    """Test force deleting a project with tasks using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create Project C with Task 2 and Task 3
    result_c = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Project C'])
    project_c_data = json.loads(result_c.output)['data']
    project_c_slug = project_c_data['slug']
    result_task2 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_c_slug, '--name', 'Task 2'])
    task_2_data = json.loads(result_task2.output)['data']
    task_2_slug = task_2_data['slug']
    result_task3 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_c_slug, '--name', 'Task 3'])
    task_3_data = json.loads(result_task3.output)['data']
    task_3_slug = task_3_data['slug']

    # Attempt delete without force (using slug) (should fail)
    result_del_noforce = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_c_slug])
    # Expect non-zero exit code because --force is missing
    assert result_del_noforce.exit_code != 0
    # Check stderr for the specific error message
    assert "Error: Deleting a project is irreversible" in result_del_noforce.stderr
    assert "--force" in result_del_noforce.stderr

    # Attempt delete with force (using slug) (should succeed)
    result_del_force = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'delete', project_c_slug, '--force'])
    assert result_del_force.exit_code == 0
    response_del_force = json.loads(result_del_force.output)
    assert response_del_force['status'] == 'success'
    assert "deleted" in response_del_force['message']

    # Verify Project C is gone (using slug)
    result_show_c = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_c_slug])
    assert json.loads(result_show_c.output)['status'] == 'error'
    assert "not found" in json.loads(result_show_c.output)['message']

    # Verify Task 2 is gone (using project slug and task slug)
    # Need to use the original project slug here as the project is gone
    result_show_t2 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_c_slug, task_2_slug])
    assert json.loads(result_show_t2.output)['status'] == 'error'
    # The error should come from the project resolver first
    assert "Project not found with identifier" in json.loads(result_show_t2.output)[
        'message']

    # Verify Task 3 is gone (using project slug and task slug)
    result_show_t3 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_c_slug, task_3_slug])
    assert json.loads(result_show_t3.output)['status'] == 'error'
    assert "Project not found with identifier" in json.loads(result_show_t3.output)[
        'message']


def test_cli_project_delete_cascade_workflow(cli_runner_env):
    """Verify 'project delete --force' cascades deletes through CLI."""
    runner, db_path = cli_runner_env

    # 1. Setup Project
    res_proj = runner.invoke(cli, ['--db-path', db_path, '--format',
                             'json', 'project', 'create', '--name', 'Cascade Proj'])
    assert res_proj.exit_code == 0
    proj_data = json.loads(res_proj.output)['data']
    proj_slug = proj_data['slug']
    proj_id = proj_data['id']

    # 2. Setup Task
    res_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json',
                             'task', 'create', '--project', proj_slug, '--name', 'Cascade Task'])
    assert res_task.exit_code == 0
    task_data = json.loads(res_task.output)['data']
    task_slug = task_data['slug']
    task_id = task_data['id']

    # 3. Setup Task Note
    res_task_note = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'note',
                                  'add', '--task', task_slug, '--project', proj_slug, '--content', 'Note on task'])
    assert res_task_note.exit_code == 0
    task_note_id = json.loads(res_task_note.output)['data']['id']

    # 4. Setup Project Note
    res_proj_note = runner.invoke(cli, ['--db-path', db_path, '--format', 'json',
                                  'note', 'add', '--project', proj_slug, '--content', 'Note on project'])
    assert res_proj_note.exit_code == 0
    proj_note_id = json.loads(res_proj_note.output)['data']['id']

    # 5. Setup Task Metadata
    metadata_key = 'cascade_key'
    metadata_value = 'cascade_value'
    res_meta = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task',
                                   'metadata', 'set', task_id,  # Use task_id argument
                                   '--key', metadata_key,    # Use --key option
                                   '--value', metadata_value])  # Use --value option
    assert res_meta.exit_code == 0, f"Metadata set failed: {res_meta.output}"

    # 6. Setup Subtask
    subtask_name = 'Cascade Subtask'
    res_subtask = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task',
                                      'subtask', 'create', task_id,  # Use 'create' and task_id
                                      '--name', subtask_name])
    assert res_subtask.exit_code == 0, f"Subtask creation failed: {res_subtask.output}"
    subtask_id = json.loads(res_subtask.output)['data']['id']

    # 7. Setup Dependency Task
    res_dep_task = runner.invoke(cli, ['--db-path', db_path, '--format',
                                 'json', 'task', 'create', '--project', proj_slug, '--name', 'Dep Task'])
    assert res_dep_task.exit_code == 0
    dep_task_data = json.loads(res_dep_task.output)['data']
    dep_task_slug = dep_task_data['slug']
    dep_task_id = dep_task_data['id']

    # 8. Setup Dependency (task depends on dep_task)
    res_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task',
                                  'dependency', 'add', proj_slug, task_slug,  # Dependent task
                                  '--depends-on', dep_task_slug])  # Dependency task via option
    assert res_dep.exit_code == 0, f"Dependency add failed: {res_dep.output}"

    # 9. Delete Project with --force
    res_delete = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'delete', proj_slug, '--force'])
    assert res_delete.exit_code == 0
    assert json.loads(res_delete.output)['status'] == 'success'

    # 10. Verify everything is gone via direct DB check
    conn = init_db(db_path)
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM projects WHERE id = ?", (proj_id,)).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = ?", (task_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM tasks WHERE id = ?",
                            # Other task in project also gone
                            (dep_task_id,)).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM notes WHERE id = ?", (task_note_id,)).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM notes WHERE id = ?", (proj_note_id,)).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM task_metadata WHERE task_id = ?", (task_id,)).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM subtasks WHERE id = ?", (subtask_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM task_dependencies WHERE task_id = ? OR dependency_id = ?",
                            (task_id, task_id)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM task_dependencies WHERE task_id = ? OR dependency_id = ?",
                            (dep_task_id, dep_task_id)).fetchone()[0] == 0
    finally:
        conn.close()


def test_cli_task_delete_cascade_workflow(cli_runner_env):
    """Verify 'task delete --force' cascades deletes through CLI."""
    runner, db_path = cli_runner_env

    # 1. Setup Project
    res_proj = runner.invoke(cli, ['--db-path', db_path, '--format',
                             'json', 'project', 'create', '--name', 'Task Cascade Proj'])
    assert res_proj.exit_code == 0
    proj_data = json.loads(res_proj.output)['data']
    proj_slug = proj_data['slug']
    proj_id = proj_data['id']

    # 2. Setup Task to Delete
    res_task_del = runner.invoke(cli, ['--db-path', db_path, '--format', 'json',
                                 'task', 'create', '--project', proj_slug, '--name', 'Task To Delete'])
    assert res_task_del.exit_code == 0
    task_del_data = json.loads(res_task_del.output)['data']
    task_del_slug = task_del_data['slug']
    task_del_id = task_del_data['id']

    # 3. Setup Other Task (for dependency)
    res_task_other = runner.invoke(cli, ['--db-path', db_path, '--format',
                                   'json', 'task', 'create', '--project', proj_slug, '--name', 'Other Task'])
    assert res_task_other.exit_code == 0
    task_other_data = json.loads(res_task_other.output)['data']
    task_other_slug = task_other_data['slug']
    task_other_id = task_other_data['id']

    # 4. Setup Task Note
    res_task_note = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'note', 'add',
                                  '--task', task_del_slug, '--project', proj_slug, '--content', 'Note on task to delete'])
    assert res_task_note.exit_code == 0
    task_note_id = json.loads(res_task_note.output)['data']['id']

    # 5. Setup Task Metadata
    metadata_key_task = 'cascade_key_task'
    metadata_value_task = 'cascade_value_task'
    res_meta = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata',
                                   'set', task_del_id,  # Use task_id argument
                                   '--key', metadata_key_task,  # Use --key option
                                   '--value', metadata_value_task])  # Use --value option
    assert res_meta.exit_code == 0, f"Metadata set failed: {res_meta.output}"

    # 6. Setup Subtask
    subtask_name_del = 'Cascade Subtask TaskDel'
    res_subtask = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task',
                                      'subtask', 'create', task_del_id,  # Use 'create' and task_del_id
                                      '--name', subtask_name_del])
    assert res_subtask.exit_code == 0, f"Subtask creation failed: {res_subtask.output}"
    subtask_id = json.loads(res_subtask.output)['data']['id']

    # 7. Setup Dependency (task_del depends on other_task)
    res_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task',
                                  'dependency', 'add', proj_slug, task_del_slug,  # Dependent task
                                  '--depends-on', task_other_slug])  # Dependency task via option
    assert res_dep.exit_code == 0, f"Dependency add failed: {res_dep.output}"

    # 8. Delete Task with --force
    res_delete = runner.invoke(cli, ['--db-path', db_path, '--format',
                               'json', 'task', 'delete', proj_slug, task_del_slug, '--force'])
    assert res_delete.exit_code == 0
    assert json.loads(res_delete.output)['status'] == 'success'

    # 9. Verify associated data is gone, but project and other task remain
    conn = init_db(db_path)
    try:
        # Verify project still exists
        assert conn.execute(
            "SELECT COUNT(*) FROM projects WHERE id = ?", (proj_id,)).fetchone()[0] == 1
        # Verify task_to_delete is gone
        assert conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = ?", (task_del_id,)).fetchone()[0] == 0
        # Verify other_task still exists
        assert conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = ?", (task_other_id,)).fetchone()[0] == 1
        # Verify task note is gone
        assert conn.execute(
            "SELECT COUNT(*) FROM notes WHERE id = ?", (task_note_id,)).fetchone()[0] == 0
        # Verify metadata is gone
        assert conn.execute(
            "SELECT COUNT(*) FROM task_metadata WHERE task_id = ?", (task_del_id,)).fetchone()[0] == 0
        # Verify subtask is gone
        assert conn.execute(
            "SELECT COUNT(*) FROM subtasks WHERE id = ?", (subtask_id,)).fetchone()[0] == 0
        # Verify dependency involving deleted task is gone
        assert conn.execute("SELECT COUNT(*) FROM task_dependencies WHERE task_id = ? OR dependency_id = ?",
                            (task_del_id, task_del_id)).fetchone()[0] == 0
    finally:
        conn.close()
