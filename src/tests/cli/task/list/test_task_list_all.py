# tests/cli/task/list/test_task_list_all.py
import json
from pm.cli.__main__ import cli
from pm.core.types import TaskStatus

# Fixture `setup_tasks_for_all_list_test` moved to conftest.py


# --- Tests for --all flag ---

def test_task_list_all_shows_all_tasks(setup_tasks_for_all_list_test):
    """Test 'task list --all' shows all tasks from all projects, regardless of status or project status."""
    runner, db_path, projects, tasks, expected_task_keys = setup_tasks_for_all_list_test

    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--all'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    listed_tasks = response["data"]

    assert len(listed_tasks) == len(
        expected_task_keys), f"Expected {len(expected_task_keys)} tasks, found {len(listed_tasks)}"

    listed_slugs = {t['slug'] for t in listed_tasks}
    expected_slugs = {tasks[key]['slug'] for key in expected_task_keys}
    assert listed_slugs == expected_slugs


def test_task_list_all_overrides_project(setup_tasks_for_all_list_test):
    """Test 'task list --all' overrides the --project flag."""
    runner, db_path, projects, tasks, expected_task_keys = setup_tasks_for_all_list_test
    active_project_slug = projects["Active Project"]['slug']

    result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json',
                           'task', 'list', '--all', '--project', active_project_slug])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    listed_tasks = response["data"]

    # Should still list all tasks, ignoring --project
    assert len(listed_tasks) == len(expected_task_keys)
    listed_slugs = {t['slug'] for t in listed_tasks}
    expected_slugs = {tasks[key]['slug'] for key in expected_task_keys}
    assert listed_slugs == expected_slugs


def test_task_list_all_overrides_status_filters(setup_tasks_for_all_list_test):
    """Test 'task list --all' overrides status filters like --status, --completed, --abandoned."""
    runner, db_path, projects, tasks, expected_task_keys = setup_tasks_for_all_list_test
    expected_slugs = {tasks[key]['slug'] for key in expected_task_keys}
    expected_count = len(expected_task_keys)

    # Test overriding --status
    result_status = runner.invoke(cli, ['--db-path', db_path, '--format',
                                  'json', 'task', 'list', '--all', '--status', TaskStatus.COMPLETED.value])
    assert result_status.exit_code == 0
    assert len(json.loads(result_status.output)['data']) == expected_count
    assert {t['slug'] for t in json.loads(result_status.output)[
        'data']} == expected_slugs

    # Test overriding --completed
    # --completed flag exists but should be ignored
    result_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--all', '--completed'])
    assert result_completed.exit_code == 0
    assert len(json.loads(result_completed.output)['data']) == expected_count
    assert {t['slug'] for t in json.loads(result_completed.output)[
        'data']} == expected_slugs

    # Test overriding --abandoned
    # --abandoned flag exists but should be ignored
    result_abandoned = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--all', '--abandoned'])
    assert result_abandoned.exit_code == 0
    assert len(json.loads(result_abandoned.output)['data']) == expected_count
    assert {t['slug'] for t in json.loads(result_abandoned.output)[
        'data']} == expected_slugs

    # Test overriding both --completed and --abandoned
    result_both = runner.invoke(cli, ['--db-path', db_path, '--format',
                                'json', 'task', 'list', '--all', '--completed', '--abandoned'])
    assert result_both.exit_code == 0
    assert len(json.loads(result_both.output)['data']) == expected_count
    assert {t['slug'] for t in json.loads(result_both.output)[
        'data']} == expected_slugs


def test_task_list_all_with_display_options(setup_tasks_for_all_list_test):
    """Test 'task list --all' works with display options like --id and --description."""
    runner, db_path, projects, tasks, expected_task_keys = setup_tasks_for_all_list_test

    result = runner.invoke(cli, ['--db-path', db_path, '--format',
                           'text', 'task', 'list', '--all', '--id', '--description'])
    assert result.exit_code == 0
    output = result.output

    # Check headers are present
    assert "ID" in output
    assert "DESCRIPTION" in output
    # Should be present in text format when listing across projects
    assert "PROJECT_SLUG" in output

    # Check all tasks are mentioned (using slugs as identifiers)
    for key in expected_task_keys:
        assert tasks[key]['slug'] in output


def test_task_list_all_with_text_format(setup_tasks_for_all_list_test):
    """Test 'task list --all --format text' includes project slugs."""
    runner, db_path, projects, tasks, expected_task_keys = setup_tasks_for_all_list_test

    result = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--all'])
    assert result.exit_code == 0
    output = result.output

    # Check header is present
    assert "PROJECT_SLUG" in output

    # Check both project slugs appear in the output
    assert projects["Active Project"]['slug'] in output
    assert projects["Inactive Project"]['slug'] in output

    # Check all tasks are mentioned (using slugs as identifiers)
    for key in expected_task_keys:
        assert tasks[key]['slug'] in output
