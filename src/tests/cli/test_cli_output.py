import json
import pytest
from click.testing import CliRunner

from pm.cli.__main__ import cli
from pm.storage.db import init_db

# --- Fixtures ---


@pytest.fixture(scope="function")
def cli_runner_env(tmp_path):
    """Provides a CliRunner and an initialized temporary DB path for tests."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    return runner, db_path


@pytest.fixture(scope="function")
def output_test_setup(cli_runner_env):
    """Sets up projects and tasks with various statuses for output testing."""
    runner, db_path = cli_runner_env
    setup_data = {}

    # Create ACTIVE project
    result_proj_active = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                             '--name', 'Format Active Proj', '--description', 'Active Desc', '--status', 'ACTIVE'])
    proj_active_data = json.loads(result_proj_active.output)['data']
    setup_data['proj_active_id'] = proj_active_data['id']
    setup_data['proj_active_slug'] = proj_active_data['slug']

    # Create COMPLETED project (will be updated to ARCHIVED)
    result_proj_completed = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                                '--name', 'Format Completed Proj', '--description', 'Completed Desc', '--status', 'COMPLETED'])
    proj_completed_data = json.loads(result_proj_completed.output)['data']
    # Store ID before update
    setup_data['proj_archived_id'] = proj_completed_data['id']
    # Store slug before update
    setup_data['proj_archived_slug'] = proj_completed_data['slug']

    # Create CANCELLED project
    result_proj_cancelled = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                                '--name', 'Format Cancelled Proj', '--description', 'Cancelled Desc', '--status', 'CANCELLED'])
    proj_cancelled_data = json.loads(result_proj_cancelled.output)['data']
    setup_data['proj_cancelled_id'] = proj_cancelled_data['id']
    setup_data['proj_cancelled_slug'] = proj_cancelled_data['slug']

    # Update COMPLETED project to ARCHIVED
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'update', setup_data['proj_archived_slug'], '--status', 'ARCHIVED'])

    # Create ACTIVE task in ACTIVE project
    result_task_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', setup_data['proj_active_slug'], '--name', 'Format Active Task', '--status', 'IN_PROGRESS'])
    task_active_data = json.loads(result_task_active.output)['data']
    setup_data['task_active_id'] = task_active_data['id']
    setup_data['task_active_slug'] = task_active_data['slug']

    # Create COMPLETED task in ACTIVE project
    result_task_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', setup_data['proj_active_slug'], '--name', 'Format Completed Task', '--status', 'COMPLETED'])
    task_completed_data = json.loads(result_task_completed.output)['data']
    setup_data['task_completed_id'] = task_completed_data['id']
    setup_data['task_completed_slug'] = task_completed_data['slug']

    # Create task in CANCELLED project
    result_task_cancelled = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', setup_data['proj_cancelled_slug'], '--name', 'Cancelled Task'])
    task_cancelled_data = json.loads(result_task_cancelled.output)['data']
    setup_data['task_cancelled_id'] = task_cancelled_data['id']
    setup_data['task_cancelled_slug'] = task_cancelled_data['slug']

    return runner, db_path, setup_data


# --- Output Format Tests ---

def test_project_list_text_defaults(output_test_setup):
    """Test default 'project list' text output (hides non-active)."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result.exit_code == 0
    output = result.output
    assert "ID" not in output
    assert "DESCRIPTION" not in output
    assert "Active Desc" not in output
    assert data['proj_active_slug'] in output
    assert data['proj_archived_slug'] not in output  # Archived (was Completed)
    assert data['proj_cancelled_slug'] not in output


def test_project_list_text_flags(output_test_setup):
    """Test 'project list' text output with various flags."""
    runner, db_path, data = output_test_setup

    # Test with --completed
    result_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--completed'])
    assert result_completed.exit_code == 0
    output_completed = result_completed.output
    assert "ID" not in output_completed
    assert "DESCRIPTION" not in output_completed
    assert data['proj_active_slug'] in output_completed
    # Is ARCHIVED, not COMPLETED
    assert data['proj_archived_slug'] not in output_completed
    assert data['proj_cancelled_slug'] not in output_completed

    # Test with --id and --completed
    result_id_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed'])
    assert result_id_completed.exit_code == 0
    output_id_completed = result_id_completed.output
    assert "ID" in output_id_completed
    assert "DESCRIPTION" not in output_id_completed
    assert data['proj_active_slug'] in output_id_completed
    # FIX: Assert NOT IN because it's ARCHIVED
    assert data['proj_archived_slug'] not in output_id_completed
    assert data['proj_cancelled_slug'] not in output_id_completed

    # Test with --description
    result_desc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--description'])
    assert result_desc.exit_code == 0
    output_desc = result_desc.output
    assert "ID" not in output_desc
    assert "DESCRIPTION" in output_desc
    assert "Active Desc" in output_desc
    assert data['proj_active_slug'] in output_desc
    assert data['proj_archived_slug'] not in output_desc
    assert data['proj_cancelled_slug'] not in output_desc

    # Test with --id, --completed, --description
    result_id_comp_desc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed', '--description'])
    assert result_id_comp_desc.exit_code == 0
    output_id_comp_desc = result_id_comp_desc.output
    assert "ID" in output_id_comp_desc
    assert "DESCRIPTION" in output_id_comp_desc
    assert "Active Desc" in output_id_comp_desc
    # FIX: Assert NOT IN description because it's ARCHIVED
    assert "Completed Desc" not in output_id_comp_desc
    assert data['proj_active_slug'] in output_id_comp_desc
    # FIX: Assert NOT IN slug because it's ARCHIVED
    assert data['proj_archived_slug'] not in output_id_comp_desc
    assert data['proj_cancelled_slug'] not in output_id_comp_desc

    # Test with --archived
    result_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--archived'])
    assert result_arch.exit_code == 0
    output_arch = result_arch.output
    assert "ID" not in output_arch
    assert "DESCRIPTION" not in output_arch
    assert data['proj_active_slug'] in output_arch
    assert data['proj_archived_slug'] in output_arch  # Archived shown
    assert data['proj_cancelled_slug'] not in output_arch

    # Test with --cancelled
    result_canc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--cancelled'])
    assert result_canc.exit_code == 0
    output_canc = result_canc.output
    assert data['proj_active_slug'] in output_canc
    assert data['proj_archived_slug'] not in output_canc
    assert data['proj_cancelled_slug'] in output_canc  # Cancelled shown

    # Test with --completed, --archived, --cancelled (shows all)
    result_all_status = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--completed', '--archived', '--cancelled'])
    assert result_all_status.exit_code == 0
    output_all_status = result_all_status.output
    assert "ID" not in output_all_status
    assert "DESCRIPTION" not in output_all_status
    assert data['proj_active_slug'] in output_all_status
    assert data['proj_archived_slug'] in output_all_status  # Archived
    assert data['proj_cancelled_slug'] in output_all_status  # Cancelled

    # Test with all flags (--id, --desc, --completed, --archived, --cancelled)
    result_all_flags = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--description', '--completed', '--archived', '--cancelled'])
    assert result_all_flags.exit_code == 0
    output_all_flags = result_all_flags.output
    assert "ID" in output_all_flags
    assert "DESCRIPTION" in output_all_flags
    assert data['proj_active_slug'] in output_all_flags
    assert data['proj_archived_slug'] in output_all_flags  # Archived
    assert data['proj_cancelled_slug'] in output_all_flags  # Cancelled
    assert "Active Desc" in output_all_flags
    assert "Completed Desc" in output_all_flags  # Description of Archived project
    assert "Cancelled Desc" in output_all_flags


def test_project_show_text(output_test_setup):
    """Test 'project show' text output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', data['proj_active_slug']])
    assert result.exit_code == 0
    output = result.output
    assert f"Id:          {data['proj_active_id']}" in output
    assert "Name:        Format Active Proj" in output
    assert f"Slug:        {data['proj_active_slug']}" in output
    assert "Description: Active Desc" in output
    assert "Status:      Active" in output  # Expect title case


def test_task_list_text_defaults(output_test_setup):
    """Test default 'task list' text output."""
    runner, db_path, data = output_test_setup

    # Test within the active project
    result_active_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', data['proj_active_slug']])
    assert result_active_proj.exit_code == 0
    output_active_proj = result_active_proj.output
    assert "ID" not in output_active_proj
    assert "DESCRIPTION" not in output_active_proj
    assert data['task_active_slug'] in output_active_proj
    assert data['task_completed_slug'] not in output_active_proj

    # Test without project filter (should only show tasks from ACTIVE projects)
    result_all_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list'])
    assert result_all_proj.exit_code == 0
    output_all_proj = result_all_proj.output
    assert data['task_active_slug'] in output_all_proj
    assert data['task_completed_slug'] not in output_all_proj
    # Task from cancelled project
    assert data['task_cancelled_slug'] not in output_all_proj


def test_task_list_text_flags(output_test_setup):
    """Test 'task list' text output with flags."""
    runner, db_path, data = output_test_setup

    # Test with --completed (within active project)
    result_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', data['proj_active_slug'], '--completed'])
    assert result_completed.exit_code == 0
    output_completed = result_completed.output
    assert data['task_active_slug'] in output_completed
    assert data['task_completed_slug'] in output_completed

    # Test with --inactive (should show task from cancelled project)
    result_inactive = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--inactive'])
    assert result_inactive.exit_code == 0
    output_inactive = result_inactive.output
    assert data['task_active_slug'] in output_inactive
    # Completed still hidden by default
    assert data['task_completed_slug'] not in output_inactive
    # Task from cancelled project shown
    assert data['task_cancelled_slug'] in output_inactive

    # Test with --inactive and --completed
    result_inactive_comp = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--inactive', '--completed'])
    assert result_inactive_comp.exit_code == 0
    output_inactive_comp = result_inactive_comp.output
    assert data['task_active_slug'] in output_inactive_comp
    assert data['task_completed_slug'] in output_inactive_comp
    assert data['task_cancelled_slug'] in output_inactive_comp

    # Test with --id and --description (within active project)
    result_id_desc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', data['proj_active_slug'], '--id', '--description'])
    assert result_id_desc.exit_code == 0
    output_id_desc = result_id_desc.output
    assert "ID" in output_id_desc
    assert "DESCRIPTION" in output_id_desc
    assert data['task_active_slug'] in output_id_desc
    # Completed still hidden
    assert data['task_completed_slug'] not in output_id_desc
    assert "Format Active Task" in output_id_desc


def test_task_show_text(output_test_setup):
    """Test 'task show' text output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'show', data['proj_active_slug'], data['task_active_slug']])
    assert result.exit_code == 0
    output = result.output
    # Adjusted spacing
    assert f"Id:           {data['task_active_id']}" in output
    # Changed to check for Slug
    assert f"Project Slug: {data['proj_active_slug']}" in output
    assert "Name:         Format Active Task" in output  # Adjusted spacing
    # Adjusted spacing
    assert f"Slug:         {data['task_active_slug']}" in output
    assert "Description: " in output  # Default description is empty
    assert "Status:       In progress" in output  # Adjusted spacing


def test_project_list_json(output_test_setup):
    """Test 'project list' JSON output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list', '--completed', '--archived', '--cancelled'])
    assert result.exit_code == 0
    output_data = json.loads(result.output)['data']
    assert len(output_data) == 3  # Active, Archived, Cancelled
    slugs = {p['slug'] for p in output_data}
    assert data['proj_active_slug'] in slugs
    assert data['proj_archived_slug'] in slugs
    assert data['proj_cancelled_slug'] in slugs


def test_project_show_json(output_test_setup):
    """Test 'project show' JSON output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', data['proj_active_slug']])
    assert result.exit_code == 0
    output_data = json.loads(result.output)['data']
    assert output_data['id'] == data['proj_active_id']
    assert output_data['slug'] == data['proj_active_slug']
    assert output_data['name'] == 'Format Active Proj'
    assert output_data['status'] == 'ACTIVE'


def test_task_list_json(output_test_setup):
    """Test 'task list' JSON output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--inactive', '--completed'])
    assert result.exit_code == 0
    output_data = json.loads(result.output)['data']
    assert len(output_data) == 3  # Active, Completed, Cancelled Task
    slugs = {t['slug'] for t in output_data}
    assert data['task_active_slug'] in slugs
    assert data['task_completed_slug'] in slugs
    assert data['task_cancelled_slug'] in slugs


def test_task_show_json(output_test_setup):
    """Test 'task show' JSON output."""
    runner, db_path, data = output_test_setup
    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', data['proj_active_slug'], data['task_active_slug']])
    assert result.exit_code == 0
    output_data = json.loads(result.output)['data']
    assert output_data['id'] == data['task_active_id']
    assert output_data['slug'] == data['task_active_slug']
    assert output_data['name'] == 'Format Active Task'
    assert output_data['status'] == 'IN_PROGRESS'
    assert output_data['project_id'] == data['proj_active_id']


def test_default_output_is_text(output_test_setup):
    """Test that the default output format is text when --format is omitted."""
    runner, db_path, data = output_test_setup
    # Invoke 'project show' without specifying --format
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', data['proj_active_slug']])
    assert result.exit_code == 0
    output = result.output.strip()  # Strip leading/trailing whitespace

    # Basic check: Should not look like JSON
    assert not output.startswith('{')
    assert not output.endswith('}')

    # Check for text formatting characteristics (key-value pairs from _format_dict_as_text)
    assert "Name:        Format Active Proj" in output
    assert f"Slug:        {data['proj_active_slug']}" in output
    assert "Status:      Active" in output  # Expect title case
