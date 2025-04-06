import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.models import SubtaskTemplate
# For setup/verification
from pm.storage import init_db, create_subtask_template, list_subtasks

# --- Helper Functions for Setup (using CLI) ---


def _create_project_cli(runner, db_path, name):
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'project', 'create', '--name', name
    ])
    assert result.exit_code == 0, f"Helper failed to create project '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing project create output: {e}\nOutput: {result.output}")


def _create_task_cli(runner, db_path, project_slug_or_id, name):
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'create', '--project', project_slug_or_id, '--name', name
    ])
    assert result.exit_code == 0, f"Helper failed to create task '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing task create output: {e}\nOutput: {result.output}")


def _create_template_cli(runner, db_path, name, description=None):
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'create', '--name', name,
        *(['--description', description] if description else [])
    ])
    assert result.exit_code == 0, f"Helper failed to create template '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing template create output: {e}\nOutput: {result.output}")

# --- Test Cases ---


def test_template_apply_success(cli_runner_env):
    runner, db_path = cli_runner_env

    # Setup: Project, Task, Template
    project_data = _create_project_cli(runner, db_path, "Apply Project")
    task_data = _create_task_cli(
        runner, db_path, project_data["id"], "Apply Task")
    template_data = _create_template_cli(runner, db_path, "Apply Template")
    task_id = task_data["id"]
    template_id = template_data["id"]

    # Setup: Subtask Templates (using direct storage)
    subtask_template_details = {"ST One": True, "ST Two": False}
    created_subtask_template_ids = set()
    with init_db(db_path) as conn:
        for name, required in subtask_template_details.items():
            subtask_tmpl = SubtaskTemplate(
                id=str(uuid.uuid4()),
                template_id=template_id,
                name=name,
                description=f"Desc {name}",
                required_for_completion=required
            )
            created = create_subtask_template(conn, subtask_tmpl)
            created_subtask_template_ids.add(created.id)

    # Run the apply command
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'apply', template_id, '--task', task_id
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == len(subtask_template_details)

        # Verify details of created subtasks from output
        created_subtask_names = {st["name"] for st in output_data["data"]}
        assert created_subtask_names == set(subtask_template_details.keys())
        st_one = next(
            (st for st in output_data["data"] if st["name"] == "ST One"), None)
        assert st_one is not None
        assert st_one["task_id"] == task_id
        assert st_one["required_for_completion"] is True
        st_two = next(
            (st for st in output_data["data"] if st["name"] == "ST Two"), None)
        assert st_two is not None
        assert st_two["task_id"] == task_id
        assert st_two["required_for_completion"] is False

    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtasks = list_subtasks(conn, task_id=task_id)
        assert len(db_subtasks) == len(subtask_template_details)
        db_subtask_names = {st.name for st in db_subtasks}
        assert db_subtask_names == set(subtask_template_details.keys())


def test_template_apply_template_not_found(cli_runner_env):
    runner, db_path = cli_runner_env
    project_data = _create_project_cli(runner, db_path, "Apply Project NF")
    task_data = _create_task_cli(
        runner, db_path, project_data["id"], "Apply Task NF")
    non_existent_template_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'apply', non_existent_template_id, '--task', task_data["id"]
    ])

    assert result.exit_code == 0  # Command runs, error in JSON
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        # Check start and end of the message
        assert output_data["message"].startswith("Template ")
        assert output_data["message"].endswith(" not found")
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")


def test_template_apply_task_not_found(cli_runner_env):
    runner, db_path = cli_runner_env
    template_data = _create_template_cli(runner, db_path, "Apply Template NF")
    non_existent_task_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'apply', template_data["id"], '--task', non_existent_task_id
    ])

    assert result.exit_code == 0  # Command runs, error in JSON
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        # Check start and end of the message
        assert output_data["message"].startswith("Task ")
        assert output_data["message"].endswith(" not found")
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")


def test_template_apply_no_subtasks_in_template(cli_runner_env):
    runner, db_path = cli_runner_env
    project_data = _create_project_cli(runner, db_path, "Apply Project Empty")
    task_data = _create_task_cli(
        runner, db_path, project_data["id"], "Apply Task Empty")
    template_data = _create_template_cli(
        runner, db_path, "Apply Template Empty")  # No subtasks added

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'apply', template_data["id"], '--task', task_data["id"]
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == 0  # Expect empty list
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB - no subtasks should be created
    with init_db(db_path) as conn:
        db_subtasks = list_subtasks(conn, task_id=task_data["id"])
        assert len(db_subtasks) == 0
