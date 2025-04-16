import json
from pm.storage import init_db
# Keep if needed for direct DB checks
from pm.cli.__main__ import cli
from pm.storage.task import get_task_dependencies  # Import for verification

# --- Dependency Tests ---

# Helper function to create a task via CLI and return its slug and ID


def create_task_cli(runner, db_path, project_slug, name):
    result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                 '--project', project_slug, '--name', name])
    assert result.exit_code == 0, f"Failed to create task '{name}': {result.output}"
    data = json.loads(result.output)['data']
    return data['slug'], data['id']


def test_cli_task_create_with_dependencies(task_cli_runner_env):
    """Test 'task create --depends-on' functionality."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create dependency tasks
    dep1_slug, dep1_id = create_task_cli(
        runner, db_path, project_slug, "Dep Task 1 For Create")
    dep2_slug, dep2_id = create_task_cli(
        runner, db_path, project_slug, "Dep Task 2 For Create")

    # 1. Create task with single dependency
    result_create_single = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                               '--project', project_slug, '--name', 'Main Task Single Dep Create',
                                               '--depends-on', dep1_slug])
    assert result_create_single.exit_code == 0, f"Output: {result_create_single.output}"
    response_single = json.loads(result_create_single.output)
    assert response_single["status"] == "success"
    main_task_single_id = response_single["data"]["id"]
    assert f"Dependencies added: {dep1_slug}" in response_single["message"]

    # Verify dependency using direct storage call
    conn = init_db(db_path)
    deps_single = get_task_dependencies(conn, main_task_single_id)
    conn.close()
    assert len(deps_single) == 1
    assert deps_single[0].id == dep1_id

    # 2. Create task with multiple dependencies
    result_create_multi = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                              '--project', project_slug, '--name', 'Main Task Multi Dep Create',
                                              '--depends-on', dep1_slug, '--depends-on', dep2_slug])
    assert result_create_multi.exit_code == 0, f"Output: {result_create_multi.output}"
    response_multi = json.loads(result_create_multi.output)
    assert response_multi["status"] == "success"
    main_task_multi_slug = response_multi["data"]["slug"]
    assert "Dependencies added: " in response_multi["message"]
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
    non_existent_slug = "no-such-task-create"
    result_create_nonexist = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                                 '--project', project_slug, '--name', 'Task Bad Dep Create',
                                                 '--depends-on', dep1_slug,  # One valid
                                                 '--depends-on', non_existent_slug])  # One invalid
    assert result_create_nonexist.exit_code == 0  # Command still succeeds overall
    response_nonexist = json.loads(result_create_nonexist.output)
    assert response_nonexist["status"] == "success"  # Task created
    task_bad_dep_id = response_nonexist["data"]["id"]
    assert "Warning: Failed to add dependencies:" in response_nonexist["message"]
    assert f"'{non_existent_slug}'" in response_nonexist["message"]
    assert "Warning: Failed to add some dependencies:" in result_create_nonexist.stderr
    assert f"'{non_existent_slug}'" in result_create_nonexist.stderr
    assert "UsageError" in result_create_nonexist.stderr
    assert "not found" in result_create_nonexist.stderr
    # Valid one added
    assert f"Dependencies added: {dep1_slug}" in response_nonexist["message"]

    # Verify only the valid dependency exists
    conn = init_db(db_path)
    deps_bad = get_task_dependencies(conn, task_bad_dep_id)
    conn.close()
    assert len(deps_bad) == 1
    assert deps_bad[0].id == dep1_id


def test_cli_task_dependency_add_remove(task_cli_runner_env):
    """Test 'task dependency add' and 'task dependency remove' functionality."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create tasks
    task_a_slug, task_a_id = create_task_cli(
        runner, db_path, project_slug, "Task A Dep AddRemove")
    task_b_slug, task_b_id = create_task_cli(
        runner, db_path, project_slug, "Task B Dep AddRemove")

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


def test_cli_task_circular_dependency_prevention(task_cli_runner_env):
    """Test circular dependency prevention via 'dependency add'."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create tasks
    task_c_slug, _ = create_task_cli(
        runner, db_path, project_slug, "Task C Circular")
    task_d_slug, _ = create_task_cli(
        runner, db_path, project_slug, "Task D Circular")

    # Create C -> D dependency first
    runner.invoke(cli, ['--db-path', db_path, 'task', 'dependency', 'add',
                        project_slug, task_c_slug, '--depends-on', task_d_slug])

    # Attempt to add D -> C dependency (should fail)
    result_circ = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'add',
                                      project_slug, task_d_slug, '--depends-on', task_c_slug])
    assert result_circ.exit_code == 0  # Command itself runs
    response_circ = json.loads(result_circ.output)
    assert response_circ["status"] == "error"  # But reports an error
    assert "circular reference" in response_circ["message"]


def test_cli_task_self_dependency_prevention(task_cli_runner_env):
    """Test prevention of self-dependencies via CLI."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create task
    task_e_slug, _ = create_task_cli(
        runner, db_path, project_slug, "Task E SelfDep")

    # Attempt self-dependency during creation (indirectly, by depending on non-existent self)
    create_self_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                          '--project', project_slug, '--name', 'Task Self Create',
                                          '--depends-on', 'task-self-create'])  # Depends on its own future slug
    assert create_self_dep.exit_code == 0  # Command runs but fails dependency add
    create_response = json.loads(create_self_dep.output)
    assert create_response['status'] == 'success'  # Task created
    assert "Warning: Failed to add dependencies:" in create_response['message']
    assert "'task-self-create'" in create_response['message']
    assert "cannot depend on itself" in create_self_dep.stderr  # Check stderr

    # Attempt self-dependency via 'dependency add'
    add_self_dep = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'add',
                                       project_slug, task_e_slug, '--depends-on', task_e_slug])
    assert add_self_dep.exit_code == 0  # Command runs
    add_response = json.loads(add_self_dep.output)
    assert add_response['status'] == 'error'
    assert "cannot depend on itself" in add_response['message']


def test_cli_task_show_displays_dependencies(task_cli_runner_env):
    """Test that 'task show' includes dependencies in output."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create tasks
    task_f_slug, _ = create_task_cli(
        runner, db_path, project_slug, "Task F ShowDep")
    task_g_slug, _ = create_task_cli(
        runner, db_path, project_slug, "Task G ShowDep")
    # Create Task H depending on F and G
    result_h = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                   '--project', project_slug, '--name', 'Task H ShowDep',
                                   '--depends-on', task_f_slug, '--depends-on', task_g_slug])
    assert result_h.exit_code == 0
    task_h_slug = json.loads(result_h.output)['data']['slug']

    # Show Task H
    show_h_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_h_slug])
    assert show_h_result.exit_code == 0
    show_h_data = json.loads(show_h_result.output)['data']
    assert 'dependencies' in show_h_data
    assert isinstance(show_h_data['dependencies'], list)
    assert len(show_h_data['dependencies']) == 2
    assert set(show_h_data['dependencies']) == {task_f_slug, task_g_slug}

    # Show Task F (should have no dependencies listed)
    show_f_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_f_slug])
    assert show_f_result.exit_code == 0
    show_f_data = json.loads(show_f_result.output)['data']
    assert 'dependencies' in show_f_data
    assert isinstance(show_f_data['dependencies'], list)
    assert len(show_f_data['dependencies']) == 0


def test_cli_task_delete_blocked_by_dependency(task_cli_runner_env):
    """Test that 'task delete' is blocked if other tasks depend on it."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create tasks
    task_i_slug, task_i_id = create_task_cli(
        runner, db_path, project_slug, "Task I DeleteDep")  # The dependency
    task_j_slug, task_j_id = create_task_cli(
        runner, db_path, project_slug, "Task J DeleteDep")  # Depends on I

    # Add dependency J -> I
    runner.invoke(cli, ['--db-path', db_path, 'task', 'dependency', 'add',
                        project_slug, task_j_slug, '--depends-on', task_i_slug])

    # Attempt to delete Task I (should fail)
    delete_i_fail = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete',
                                        project_slug, task_i_slug, '--force'])
    assert delete_i_fail.exit_code == 0  # Command runs
    delete_i_fail_response = json.loads(delete_i_fail.output)
    assert delete_i_fail_response['status'] == 'error'
    assert "Cannot delete task" in delete_i_fail_response['message']
    assert "It is a dependency for other tasks" in delete_i_fail_response['message']
    # Check dependent slug
    assert f"'{task_j_slug}'" in delete_i_fail_response['message']

    # Verify Task I still exists
    show_i_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                        project_slug, task_i_slug])
    assert show_i_result.exit_code == 0
    assert json.loads(show_i_result.output)['status'] == 'success'

    # Remove the dependency J -> I
    remove_dep_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'dependency', 'remove',
                                            project_slug, task_j_slug, '--depends-on', task_i_slug])
    assert remove_dep_result.exit_code == 0
    assert json.loads(remove_dep_result.output)['status'] == 'success'

    # Attempt to delete Task I again (should succeed now)
    delete_i_success = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete',
                                           project_slug, task_i_slug, '--force'])
    assert delete_i_success.exit_code == 0, f"Output: {delete_i_success.output}"
    assert json.loads(delete_i_success.output)['status'] == 'success'
    assert "deleted" in json.loads(delete_i_success.output)['message']

    # Verify Task I is gone
    show_i_gone_result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'show',
                                             project_slug, task_i_slug])
    assert show_i_gone_result.exit_code == 0  # Command runs
    assert json.loads(show_i_gone_result.output)[
        'status'] == 'error'  # But reports error
    assert "not found" in json.loads(show_i_gone_result.output)['message']
