"""Tests for task CLI dependency commands."""

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
from pm.storage.task import get_task_dependencies  # Import for verification

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    conn.close()
    runner = CliRunner(mix_stderr=False)
    return runner, db_path

# --- Dependency Tests ---


def test_cli_task_create_with_dependencies(cli_runner_env):
    """Test 'task create --depends-on' functionality."""
    runner, db_path = cli_runner_env

    # Setup: Create a project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Dependency Test Project'])
    assert result_proj.exit_code == 0
    project_slug = json.loads(result_proj.output)['data']['slug']
    assert project_slug == "dependency-test-project"

    # Create dependency tasks
    result_dep1 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Dep Task 1'])
    assert result_dep1.exit_code == 0
    dep1_slug = json.loads(result_dep1.output)['data']['slug']
    dep1_id = json.loads(result_dep1.output)['data']['id']
    assert dep1_slug == "dep-task-1"

    result_dep2 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Dep Task 2'])
    assert result_dep2.exit_code == 0
    dep2_slug = json.loads(result_dep2.output)['data']['slug']
    dep2_id = json.loads(result_dep2.output)['data']['id']
    assert dep2_slug == "dep-task-2"

    # 1. Create task with single dependency
    result_create_single = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                               '--project', project_slug, '--name', 'Main Task Single Dep',
                                               '--depends-on', dep1_slug])  # Depend on dep1_slug
    assert result_create_single.exit_code == 0, f"Output: {result_create_single.output}"
    response_single = json.loads(result_create_single.output)
    assert response_single["status"] == "success"
    main_task_single_slug = response_single["data"]["slug"]
    main_task_single_id = response_single["data"]["id"]
    assert main_task_single_slug == "main-task-single-dep"
    assert f"Dependencies added: {dep1_slug}" in response_single["message"]

    # Verify dependency using direct storage call for simplicity
    conn = init_db(db_path)  # Use init_db for direct connection in tests
    deps_single = get_task_dependencies(conn, main_task_single_id)
    conn.close()
    assert len(deps_single) == 1
    assert deps_single[0].id == dep1_id

    # 2. Create task with multiple dependencies
    result_create_multi = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                              '--project', project_slug, '--name', 'Main Task Multi Dep',
                                              '--depends-on', dep1_slug, '--depends-on', dep2_slug])
    assert result_create_multi.exit_code == 0, f"Output: {result_create_multi.output}"
    response_multi = json.loads(result_create_multi.output)
    assert response_multi["status"] == "success"
    main_task_multi_slug = response_multi["data"]["slug"]
    main_task_multi_id = response_multi["data"]["id"]
    assert main_task_multi_slug == "main-task-multi-dep"
    # Order might vary, check both are mentioned
    assert f"Dependencies added: " in response_multi["message"]
    assert dep1_slug in response_multi["message"]
    assert dep2_slug in response_multi["message"]

    # Verify dependencies using CLI command
    result_dep_list = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'list',
                                          project_slug, main_task_multi_slug])
    assert result_dep_list.exit_code == 0
    response_dep_list = json.loads(result_dep_list.output)
    assert response_dep_list["status"] == "success"
    assert len(response_dep_list["data"]) == 2
    listed_dep_slugs = {dep['slug'] for dep in response_dep_list["data"]}
    assert dep1_slug in listed_dep_slugs
    assert dep2_slug in listed_dep_slugs

    # 3. Create task with non-existent dependency
    non_existent_slug = "no-such-task"
    result_create_nonexist = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                                 '--project', project_slug, '--name', 'Task Bad Dep',
                                                 '--depends-on', dep1_slug,  # One valid
                                                 '--depends-on', non_existent_slug])  # One invalid
    assert result_create_nonexist.exit_code == 0  # Command still succeeds overall
    response_nonexist = json.loads(result_create_nonexist.output)
    assert response_nonexist["status"] == "success"  # Task created
    task_bad_dep_slug = response_nonexist["data"]["slug"]
    task_bad_dep_id = response_nonexist["data"]["id"]
    assert task_bad_dep_slug == "task-bad-dep"
    # Check for warning message about the failed dependency
    assert "Warning: Failed to add dependencies:" in response_nonexist["message"]
    assert f"'{non_existent_slug}'" in response_nonexist["message"]
    # Check for underlying error type
    # Check specific error type name logged
    # Check for error type name
    # Check stderr for the warning about failed dependencies
    assert "Warning: Failed to add some dependencies:" in result_create_nonexist.stderr
    assert f"'{non_existent_slug}'" in result_create_nonexist.stderr
    # Check for error type name in stderr
    assert "UsageError" in result_create_nonexist.stderr  # Check for correct error type
    # Check for 'not found' message part in stderr
    assert "not found" in result_create_nonexist.stderr
    # Check that the valid dependency was still added
    assert f"Dependencies added: {dep1_slug}" in response_nonexist["message"]

    # Verify only the valid dependency exists
    conn = init_db(db_path)  # Use init_db for direct connection in tests
    deps_bad = get_task_dependencies(conn, task_bad_dep_id)
    conn.close()
    assert len(deps_bad) == 1
    assert deps_bad[0].id == dep1_id

    # 4. Test circular dependency prevention (via underlying add_task_dependency)
    # Create A -> B dependency first
    runner.invoke(cli, ['--db-path', db_path, 'task', 'dependency', 'add',
                        project_slug, dep2_slug, '--depends-on', dep1_slug])

    # Attempt to add B -> A dependency (should fail)
    result_circ = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'add',
                                      project_slug, dep1_slug, '--depends-on', dep2_slug])
    assert result_circ.exit_code == 0  # Command itself runs
    response_circ = json.loads(result_circ.output)
    assert response_circ["status"] == "error"  # But reports an error
    assert "circular reference" in response_circ["message"]


def test_cli_task_dependency_remove(cli_runner_env):
    """Test 'task dependency remove' functionality."""
    runner, db_path = cli_runner_env
    project_slug = "dep-remove-proj"
    task_a_slug = "task-a"
    task_b_slug = "task-b"

    # Setup
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'create', '--name', 'Dep Remove Proj'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task A'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task B'])
    # Add dependency A -> B
    add_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'add',
                                     project_slug, task_a_slug, '--depends-on', task_b_slug])
    assert add_result.exit_code == 0
    assert json.loads(add_result.output)['status'] == 'success'

    # Verify dependency exists
    list_result_before = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'list',
                                             project_slug, task_a_slug])
    assert len(json.loads(list_result_before.output)['data']) == 1
    assert json.loads(list_result_before.output)[
        'data'][0]['slug'] == task_b_slug

    # Remove the dependency
    remove_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'remove',
                                        project_slug, task_a_slug, '--depends-on', task_b_slug])
    assert remove_result.exit_code == 0, f"Output: {remove_result.output}"
    assert json.loads(remove_result.output)['status'] == 'success'
    assert "Dependency removed" in json.loads(remove_result.output)['message']

    # Verify dependency is gone
    list_result_after = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'list',
                                            project_slug, task_a_slug])
    assert list_result_after.exit_code == 0
    assert len(json.loads(list_result_after.output)['data']) == 0

    # Try removing non-existent dependency
    remove_again_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'remove',
                                              project_slug, task_a_slug, '--depends-on', task_b_slug])
    assert remove_again_result.exit_code == 0  # Command runs
    assert json.loads(remove_again_result.output)[
        'status'] == 'error'  # But reports error
    assert "not found" in json.loads(remove_again_result.output)['message']


def test_cli_task_self_dependency_prevention(cli_runner_env):
    """Test prevention of self-dependencies via CLI."""
    runner, db_path = cli_runner_env
    project_slug = "self-dep-proj"
    task_a_slug = "task-a"

    # Setup
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'create', '--name', 'Self Dep Proj'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task A'])

    # Attempt self-dependency during creation
    create_self_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                          '--project', project_slug, '--name', 'Task Self',
                                          '--depends-on', 'task-self'])  # Try depending on its own future slug
    # This should fail because 'task-self' doesn't exist yet to be resolved
    assert create_self_dep.exit_code == 0  # Command runs but fails dependency add
    create_response = json.loads(create_self_dep.output)
    assert create_response['status'] == 'success'  # Task created
    assert "Warning: Failed to add dependencies:" in create_response['message']
    assert "'task-self'" in create_response['message']
    # Check stderr for correct error
    assert "cannot depend on itself" in create_self_dep.stderr

    # Attempt self-dependency via 'dependency add'
    add_self_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'add',
                                       project_slug, task_a_slug, '--depends-on', task_a_slug])
    assert add_self_dep.exit_code == 0  # Command runs
    add_response = json.loads(add_self_dep.output)
    assert add_response['status'] == 'error'
    assert "cannot depend on itself" in add_response['message']


def test_cli_task_show_displays_dependencies(cli_runner_env):
    """Test that 'task show' includes dependencies in output."""
    runner, db_path = cli_runner_env
    project_slug = "show-dep-proj"
    task_a_slug = "task-a"
    task_b_slug = "task-b"
    task_c_slug = "task-c"

    # Setup
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'create', '--name', 'Show Dep Proj'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task A'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task B'])
    # Create Task C depending on A and B
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create', '--project', project_slug, '--name', 'Task C',
                        '--depends-on', task_a_slug, '--depends-on', task_b_slug])

    # Show Task C
    show_c_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_c_slug])
    assert show_c_result.exit_code == 0
    show_c_data = json.loads(show_c_result.output)['data']
    assert 'dependencies' in show_c_data
    assert isinstance(show_c_data['dependencies'], list)
    assert len(show_c_data['dependencies']) == 2
    assert set(show_c_data['dependencies']) == {task_a_slug, task_b_slug}

    # Show Task A (should have no dependencies listed)
    show_a_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_a_slug])
    assert show_a_result.exit_code == 0
    show_a_data = json.loads(show_a_result.output)['data']
    assert 'dependencies' in show_a_data
    assert isinstance(show_a_data['dependencies'], list)
    assert len(show_a_data['dependencies']) == 0


def test_cli_task_delete_blocked_by_dependency(cli_runner_env):
    """Test that 'task delete' is blocked if other tasks depend on it."""
    runner, db_path = cli_runner_env
    project_slug = "delete-dep-proj"
    task_a_slug = "task-a"  # The dependency
    task_b_slug = "task-b"  # Depends on A

    # Setup
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'create', '--name', 'Delete Dep Proj'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                  '--project', project_slug, '--name', 'Task A'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create', '--project', project_slug, '--name', 'Task B',
                        '--depends-on', task_a_slug])

    # Attempt to delete Task A (should fail)
    delete_a_fail = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete',
                                        project_slug, task_a_slug, '--force'])
    assert delete_a_fail.exit_code == 0  # Command runs
    delete_a_fail_response = json.loads(delete_a_fail.output)
    assert delete_a_fail_response['status'] == 'error'
    assert "Cannot delete task" in delete_a_fail_response['message']
    assert "It is a dependency for other tasks" in delete_a_fail_response['message']
    # Check if dependent slug is mentioned
    assert f"'{task_b_slug}'" in delete_a_fail_response['message']

    # Verify Task A still exists
    show_a_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_a_slug])
    assert show_a_result.exit_code == 0
    assert json.loads(show_a_result.output)['status'] == 'success'

    # Remove the dependency B -> A
    remove_dep_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'remove',
                                            project_slug, task_b_slug, '--depends-on', task_a_slug])
    assert remove_dep_result.exit_code == 0
    assert json.loads(remove_dep_result.output)['status'] == 'success'

    # Attempt to delete Task A again (should succeed now)
    delete_a_success = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete',
                                           project_slug, task_a_slug, '--force'])
    assert delete_a_success.exit_code == 0, f"Output: {delete_a_success.output}"
    assert json.loads(delete_a_success.output)['status'] == 'success'
    assert "deleted" in json.loads(delete_a_success.output)['message']

    # Verify Task A is gone
    show_a_gone_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                             project_slug, task_a_slug])
    assert show_a_gone_result.exit_code == 0  # Command runs
    assert json.loads(show_a_gone_result.output)[
        'status'] == 'error'  # But reports error
    assert "not found" in json.loads(show_a_gone_result.output)['message']
