import json
import os

from pm.storage import init_db, get_note
from pm.cli.__main__ import cli

# --- CLI Tests for pm note add ---


def test_note_add_inline_content(cli_runner_env):
    """Test 'pm note add' with standard inline content."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']
    note_content = "This is an inline note."

    result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', note_content])

    assert result.exit_code == 0
    output_data = json.loads(result.output)['data']
    assert output_data['content'] == note_content
    assert output_data['entity_type'] == 'task'
    assert output_data['entity_id'] == ids['task_id']

    # Verify in DB
    conn = init_db(db_path)
    note = get_note(conn, output_data['id'])
    conn.close()
    assert note is not None
    assert note.content == note_content


def test_note_add_content_from_file(cli_runner_env, tmp_path):
    """Test 'pm note add --content @filepath'."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']
    note_content = "Content from the test file.\nWith multiple lines.\nAnd special chars: !@#$%^&*()"
    filepath = tmp_path / "note_content.txt"
    filepath.write_text(note_content, encoding='utf-8')

    result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', f"@{filepath}"])  # Use @ prefix

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    output_data = json.loads(result.output)['data']
    # Check if file content was used
    assert output_data['content'] == note_content
    assert output_data['entity_type'] == 'task'
    assert output_data['entity_id'] == ids['task_id']

    # Verify in DB
    conn = init_db(db_path)
    note = get_note(conn, output_data['id'])
    conn.close()
    assert note is not None
    assert note.content == note_content


def test_note_add_content_from_file_not_found(cli_runner_env):
    """Test 'pm note add --content @filepath' with a non-existent file."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']
    filepath = "non_existent_file.txt"

    result = runner.invoke(cli, ['--db-path', db_path, 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', f"@{filepath}"])

    assert result.exit_code != 0  # Should fail
    assert "Error: File not found" in result.stderr  # Check stderr for UsageError
    assert filepath in result.stderr  # Check stderr for filename too


def test_note_add_content_from_file_permission_error(cli_runner_env, tmp_path):
    """Test 'pm note add --content @filepath' with a file lacking read permissions."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']
    filepath = tmp_path / "no_read_permission.txt"
    filepath.write_text("Cannot read this.", encoding='utf-8')
    # Change permissions to remove read access (owner only)
    os.chmod(filepath, 0o200)  # Write-only for owner

    result = runner.invoke(cli, ['--db-path', db_path, 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', f"@{filepath}"])

    # Restore permissions for cleanup if needed (though tmp_path handles it)
    os.chmod(filepath, 0o600)

    assert result.exit_code != 0  # Should fail
    assert "Error: Permission denied" in result.stderr  # Check stderr for UsageError
    # Check if filename is mentioned
    assert str(filepath.name) in result.stderr  # Check stderr for filename too


def test_note_add_content_from_file_empty_file(cli_runner_env, tmp_path):
    """Test 'pm note add --content @filepath' with an empty file."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']
    filepath = tmp_path / "empty_note.txt"
    filepath.touch()  # Create empty file

    result = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', f"@{filepath}"])

    # Expect success exit code (0) because the CLI command catches the validation error,
    # but the output should be an error JSON.
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    response = json.loads(result.output)
    assert response['status'] == 'error'
    assert "Note content cannot be empty" in response['message']

    # Verify no note was actually created in DB
    conn = init_db(db_path)
    notes = conn.execute("SELECT * FROM notes WHERE content = ''").fetchall()
    conn.close()
    assert len(notes) == 0


def test_note_add_content_at_symbol_only(cli_runner_env):
    """Test 'pm note add --content @' (invalid usage)."""
    runner, db_path, ids = cli_runner_env
    project_slug = ids['project_slug']
    task_slug = ids['task_slug']

    result = runner.invoke(cli, ['--db-path', db_path, 'note', 'add',
                                 '--project', project_slug, '--task', task_slug,
                                 '--content', '@'])

    assert result.exit_code != 0  # Should fail
    # Check stderr for UsageError
    assert "Error: File path cannot be empty" in result.stderr
