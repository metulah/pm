import pytest
import json
from click.testing import CliRunner

from pm.cli.__main__ import cli  # Main CLI entry point
from pm.storage import init_db  # For initializing the temp DB

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def runner_and_db(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test_project_tasks.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    # Return runner and db_path for tests to use
    yield runner, db_path
    # Cleanup happens automatically due to tmp_path

# --- Fixture to Setup Data using CLI ---


@pytest.fixture
def setup_projects_and_tasks_cli(runner_and_db):
    """Fixture to set up projects and tasks for testing using CLI commands."""
    runner, db_path = runner_and_db
    created_data = {}

    # Helper to run create commands and store results
    def create_via_cli(command_args, data_key):
        result = runner.invoke(
            cli, ['--db-path', db_path, '--format', 'json'] + command_args)
        assert result.exit_code == 0, f"Failed to create {data_key}: {result.output}"
        response = json.loads(result.output)
        assert response["status"] == "success"
        created_data[data_key] = response["data"]
        return response["data"]  # Return the created object data

    # Project 1 (ACTIVE)
    proj1_data = create_via_cli(
        ['project', 'create', '--name', 'Project Alpha', '--status', 'ACTIVE'], 'proj1')
    create_via_cli(['task', 'create', '--project', proj1_data['slug'],
                    '--name', 'Alpha Task 1', '--status', 'NOT_STARTED'], 'task1')
    create_via_cli(['task', 'create', '--project', proj1_data['slug'],
                    '--name', 'Alpha Task 2', '--status', 'IN_PROGRESS'], 'task2')
    create_via_cli(['task', 'create', '--project', proj1_data['slug'],
                    '--name', 'Alpha Task 3', '--status', 'COMPLETED'], 'task3')

    # Project 2 (ACTIVE)
    proj2_data = create_via_cli(
        ['project', 'create', '--name', 'Project Beta', '--status', 'ACTIVE'], 'proj2')
    create_via_cli(['task', 'create', '--project', proj2_data['slug'],
                    '--name', 'Beta Task 1', '--status', 'NOT_STARTED'], 'task4')

    # Project 3 (ARCHIVED)
    proj3_data = create_via_cli(
        ['project', 'create', '--name', 'Project Gamma', '--status', 'ARCHIVED'], 'proj3')
    create_via_cli(['task', 'create', '--project', proj3_data['slug'],
                    '--name', 'Gamma Task 1', '--status', 'NOT_STARTED'], 'task5')

    # Add runner and db_path to the returned dict for convenience in tests
    created_data['runner'] = runner
    created_data['db_path'] = db_path
    return created_data


# --- Tests ---

def test_project_tasks_list_by_slug(setup_projects_and_tasks_cli):
    """Test `pm project tasks <slug>` lists tasks for the correct project."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    task1 = setup_projects_and_tasks_cli["task1"]
    task2 = setup_projects_and_tasks_cli["task2"]
    # Completed task (task3) should not show by default

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj1['slug']])

    assert result.exit_code == 0
    # Check project slug is mentioned (depends on formatter)
    assert proj1['slug'] in result.output
    assert task1['name'] in result.output
    assert task1['slug'] in result.output
    assert task2['name'] in result.output
    assert task2['slug'] in result.output
    assert "Alpha Task 3" not in result.output  # Completed task hidden by default
    assert "Beta Task 1" not in result.output  # Task from other project
    assert "Gamma Task 1" not in result.output  # Task from inactive project


def test_project_tasks_list_by_id(setup_projects_and_tasks_cli):
    """Test `pm project tasks <id>` lists tasks for the correct project."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    task1 = setup_projects_and_tasks_cli["task1"]
    task2 = setup_projects_and_tasks_cli["task2"]

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj1['id']])

    assert result.exit_code == 0
    assert task1['name'] in result.output
    assert task2['name'] in result.output
    assert "Alpha Task 3" not in result.output
    assert "Beta Task 1" not in result.output


def test_project_tasks_list_include_completed(setup_projects_and_tasks_cli):
    """Test `pm project tasks <slug> --completed` includes completed tasks."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    task1 = setup_projects_and_tasks_cli["task1"]
    task2 = setup_projects_and_tasks_cli["task2"]
    task3 = setup_projects_and_tasks_cli["task3"]  # Completed task

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj1['slug'], '--completed'])

    assert result.exit_code == 0
    assert task1['name'] in result.output
    assert task2['name'] in result.output
    # Completed task should now be visible
    assert task3['name'] in result.output
    assert "Beta Task 1" not in result.output


def test_project_tasks_filter_by_status(setup_projects_and_tasks_cli):
    """Test `pm project tasks <slug> --status <STATUS>` filters correctly."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    task1 = setup_projects_and_tasks_cli["task1"]  # NOT_STARTED
    task2 = setup_projects_and_tasks_cli["task2"]  # IN_PROGRESS

    result = runner.invoke(cli, ['--db-path', db_path, 'project',
                           'tasks', proj1['slug'], '--status', 'IN_PROGRESS'])

    assert result.exit_code == 0
    assert task2['name'] in result.output
    assert task1['name'] not in result.output
    assert "Alpha Task 3" not in result.output  # Completed task also filtered out


def test_project_tasks_include_inactive(setup_projects_and_tasks_cli):
    """Test listing tasks for an inactive project works."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj3 = setup_projects_and_tasks_cli["proj3"]  # Archived project
    task5 = setup_projects_and_tasks_cli["task5"]

    # Running `project tasks` on an inactive project should still work
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj3['slug']])

    assert result.exit_code == 0
    assert task5['name'] in result.output

    # The --inactive flag on `project tasks` doesn't really change behavior
    # because we're already scoped to a single project. Let's confirm it doesn't break.
    result_inactive = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj3['slug'], '--inactive'])
    assert result_inactive.exit_code == 0
    assert task5['name'] in result_inactive.output


def test_project_tasks_show_id(setup_projects_and_tasks_cli):
    """Test `pm project tasks <slug> --id` shows the ID column."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    task1 = setup_projects_and_tasks_cli["task1"]

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj1['slug'], '--id'])

    assert result.exit_code == 0
    assert task1['name'] in result.output
    assert task1['id'] in result.output  # Check if the full ID is present


def test_project_tasks_show_description(setup_projects_and_tasks_cli):
    """Test `pm project tasks <slug> --description` shows the description column."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']
    proj1 = setup_projects_and_tasks_cli["proj1"]
    # Add a task with a description using the CLI helper
    desc_text = "This is a detailed description."
    task_desc_data = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                         '--project', proj1['slug'],
                                         '--name', 'Desc Task',
                                         '--description', desc_text,
                                         '--status', 'NOT_STARTED'])
    assert task_desc_data.exit_code == 0
    task_desc = json.loads(task_desc_data.output)['data']

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', proj1['slug'], '--description'])

    assert result.exit_code == 0
    assert task_desc['name'] in result.output
    assert desc_text in result.output  # Check if the description text is present


def test_project_tasks_invalid_project(setup_projects_and_tasks_cli):
    """Test `pm project tasks <invalid>` shows an error."""
    runner = setup_projects_and_tasks_cli['runner']
    db_path = setup_projects_and_tasks_cli['db_path']

    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'tasks', 'non-existent-project'])

    # Should fail (UsageError typically exits with 2)
    assert result.exit_code != 0
    # Click prints UsageError messages to stderr, including usage info.
    # We check for the specific error message part raised by the resolver.
    assert "Project not found with identifier: 'non-existent-project'" in result.stderr
