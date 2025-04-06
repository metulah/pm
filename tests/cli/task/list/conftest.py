# conftest.py for tests/cli/task/list

import pytest
import json
from click.testing import CliRunner
from pm.cli.__main__ import cli
from pm.core.types import TaskStatus
from pm.storage import init_db  # Import init_db here

# --- Fixture for standard list tests ---


@pytest.fixture
# Depends on fixture from parent conftest
def setup_tasks_for_list_test(task_cli_runner_env):
    """Fixture to set up tasks with various statuses for list tests."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    tasks = {}

    # Helper to create tasks
    def create_task(name, status=TaskStatus.NOT_STARTED):
        task_name = f"List Test - {name}"
        result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                     '--project', project_slug, '--name', task_name, '--status', status.value])
        assert result.exit_code == 0, f"Failed to create task '{task_name}': {result.output}"
        task_data = json.loads(result.output)['data']
        tasks[name] = task_data  # Store the whole dict
        # Don't return anything, just populate the tasks dict

    # Create tasks with different statuses
    create_task("Not Started", TaskStatus.NOT_STARTED)
    create_task("In Progress", TaskStatus.IN_PROGRESS)
    create_task("Blocked", TaskStatus.BLOCKED)
    # Need to go through IN_PROGRESS for these
    create_task("To Complete", TaskStatus.IN_PROGRESS)
    completed_slug = tasks["To Complete"]['slug']  # Get slug from stored dict
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update', project_slug,
                  completed_slug, '--status', TaskStatus.COMPLETED.value])
    # Corrected line 37/38
    tasks['Completed'] = json.loads(runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, completed_slug]).output)['data']

    create_task("To Abandon", TaskStatus.IN_PROGRESS)
    abandoned_slug = tasks["To Abandon"]['slug']  # Get slug from stored dict
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update', project_slug,
                  abandoned_slug, '--status', TaskStatus.ABANDONED.value])
    # Corrected line 43/44
    tasks['Abandoned'] = json.loads(runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, abandoned_slug]).output)['data']

    # Return all necessary info (Corrected indentation)
    return runner, db_path, project_slug, tasks


# --- Fixture for testing --all flag ---

@pytest.fixture
# Use tmp_path_factory directly
def setup_tasks_for_all_list_test(tmp_path_factory):
    """Fixture to set up tasks across multiple projects (active/inactive) for --all list tests.
       Creates its own isolated runner and DB."""
    # Create isolated DB and runner for this fixture
    db_path = str(tmp_path_factory.mktemp(
        "all_list_tests_db") / "test_all_list.db")
    conn = init_db(db_path)  # Need to import init_db
    conn.close()
    runner = CliRunner(mix_stderr=False)  # Use a runner local to this fixture

    projects = {}
    tasks = {}

    # Helper to create projects - uses the fixture's local runner
    def create_project(name, status="Active"):
        # Slug is generated internally, do not pass it here
        # Remove --format json again to see if it resolves the setup issue in isolation
        result = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                     '--name', name, '--status', status])
        assert result.exit_code == 0, f"Failed to create project '{name}': {result.output}"
        # Since format is no longer json, we can't parse output this way.
        # We need the slug, so fetch the project after creation.
        # This assumes the default text output includes enough info or we fetch by name.
        # For simplicity, let's assume slug generation is predictable for now,
        # or modify to fetch the project properly if needed.
        # A more robust approach would be to fetch the project by name after creation.
        # Let's try predicting the slug first.
        predicted_slug = name.lower().replace(" ", "-")
        # We still need the project_data dict for the fixture return value.
        # Fetch the project to get its ID and confirm slug.
        from pm.storage import get_project_by_slug  # Local import
        conn = init_db(db_path)
        project_obj = get_project_by_slug(conn, predicted_slug)
        conn.close()
        assert project_obj is not None, f"Could not fetch created project with predicted slug {predicted_slug}"
        project_data = {  # Reconstruct necessary data
            "id": project_obj.id,
            "name": project_obj.name,
            "slug": project_obj.slug,
            "status": project_obj.status.value,
            # Add other fields if needed by tests, though slug is primary here
        }
        projects[name] = project_data
        return project_data['slug']

    # Helper to create tasks
    def create_task(project_slug, task_name_suffix, status=TaskStatus.NOT_STARTED):
        task_name = f"All List Test - {project_slug} - {task_name_suffix}"
        # Unique key for tasks dict
        task_key = f"{project_slug}_{task_name_suffix}"
        result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                     '--project', project_slug, '--name', task_name, '--status', status.value])
        assert result.exit_code == 0, f"Failed to create task '{task_name}': {result.output}"
        task_data = json.loads(result.output)['data']
        tasks[task_key] = task_data
        return task_data['slug']

    # Helper to update task status
    def update_task_status(project_slug, task_key, new_status):
        task_slug = tasks[task_key]['slug']
        result = runner.invoke(cli, ['--db-path', db_path, 'task', 'update', project_slug,
                                     task_slug, '--status', new_status.value])
        assert result.exit_code == 0, f"Failed to update task '{task_key}' status: {result.output}"
        # Re-fetch task data to update status in our dict
        show_result = runner.invoke(
            cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, task_slug])
        tasks[task_key] = json.loads(show_result.output)['data']

    # Create Projects (Use uppercase status values matching the Enum/Choice)
    active_project_slug = create_project("Active Project", "ACTIVE")
    inactive_project_slug = create_project(
        "Inactive Project", "COMPLETED")  # Use a non-active status

    # Create Tasks in Active Project
    create_task(active_project_slug, "Not Started", TaskStatus.NOT_STARTED)
    create_task(active_project_slug, "To Complete", TaskStatus.IN_PROGRESS)
    update_task_status(
        active_project_slug, f"{active_project_slug}_To Complete", TaskStatus.COMPLETED)
    create_task(active_project_slug, "To Abandon", TaskStatus.IN_PROGRESS)
    update_task_status(
        active_project_slug, f"{active_project_slug}_To Abandon", TaskStatus.ABANDONED)

    # Create Tasks in Inactive Project
    create_task(inactive_project_slug, "Not Started", TaskStatus.NOT_STARTED)
    create_task(inactive_project_slug, "To Complete", TaskStatus.IN_PROGRESS)
    update_task_status(inactive_project_slug,
                       f"{inactive_project_slug}_To Complete", TaskStatus.COMPLETED)
    create_task(inactive_project_slug, "To Abandon", TaskStatus.IN_PROGRESS)
    update_task_status(inactive_project_slug,
                       f"{inactive_project_slug}_To Abandon", TaskStatus.ABANDONED)

    # Expected total tasks = 3 (active proj) + 3 (inactive proj) = 6
    expected_task_keys = list(tasks.keys())

    # Yield the locally created runner and db_path along with project/task info
    yield runner, db_path, projects, tasks, expected_task_keys
