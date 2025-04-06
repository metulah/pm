"""Tests for base CLI utilities, including identifier resolvers."""

import pytest
import sqlite3
import uuid
from unittest.mock import MagicMock, patch
import click

# Assume models are defined correctly for type hinting and mock return values
from pm.models import Project, Task
from pm.core.types import ProjectStatus, TaskStatus  # Import enums from core.types
# Import from common_utils
from pm.cli.common_utils import resolve_project_identifier, resolve_task_identifier, is_valid_uuid

# --- Test is_valid_uuid ---


def test_is_valid_uuid():
    """Test the UUID validation utility."""
    assert is_valid_uuid(str(uuid.uuid4())) is True
    assert is_valid_uuid("not-a-uuid") is False
    assert is_valid_uuid("project-slug") is False
    assert is_valid_uuid("") is False

# --- Test resolve_project_identifier ---


@patch('pm.cli.common_utils.get_project')  # Target common_utils
@patch('pm.cli.common_utils.get_project_by_slug')  # Target common_utils
def test_resolve_project_by_uuid(mock_get_by_slug, mock_get_by_id):
    """Test resolving project by UUID."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    project_id = str(uuid.uuid4())
    mock_project = Project(id=project_id, name="Test Project",
                           slug="test-project", status=ProjectStatus.ACTIVE)
    mock_get_by_id.return_value = mock_project

    resolved_project = resolve_project_identifier(mock_conn, project_id)

    mock_get_by_id.assert_called_once_with(mock_conn, project_id)
    mock_get_by_slug.assert_not_called()
    assert resolved_project == mock_project


@patch('pm.cli.common_utils.get_project')  # Target common_utils
@patch('pm.cli.common_utils.get_project_by_slug')  # Target common_utils
def test_resolve_project_by_slug(mock_get_by_slug, mock_get_by_id):
    """Test resolving project by slug when ID lookup fails or identifier is not UUID."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    project_slug = "test-project-slug"
    mock_project = Project(id=str(uuid.uuid4()), name="Test Project",
                           slug=project_slug, status=ProjectStatus.ACTIVE)
    mock_get_by_id.return_value = None  # Simulate ID lookup failure
    mock_get_by_slug.return_value = mock_project

    resolved_project = resolve_project_identifier(mock_conn, project_slug)

    # is_valid_uuid is called implicitly first
    mock_get_by_id.assert_not_called()  # Because it's not a UUID
    mock_get_by_slug.assert_called_once_with(mock_conn, project_slug)
    assert resolved_project == mock_project


@patch('pm.cli.common_utils.get_project')  # Target common_utils
@patch('pm.cli.common_utils.get_project_by_slug')  # Target common_utils
def test_resolve_project_not_found(mock_get_by_slug, mock_get_by_id):
    """Test resolving non-existent project identifier."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    identifier = "non-existent"
    mock_get_by_id.return_value = None
    mock_get_by_slug.return_value = None

    with pytest.raises(click.UsageError, match=f"Project not found with identifier: '{identifier}'"):
        resolve_project_identifier(mock_conn, identifier)

    mock_get_by_slug.assert_called_once_with(mock_conn, identifier)

# --- Test resolve_task_identifier ---


# Mock project object needed for task resolver tests
mock_project_obj = Project(id=str(uuid.uuid4(
)), name="Parent Project", slug="parent-project", status=ProjectStatus.ACTIVE)


@patch('pm.cli.common_utils.get_task')  # Target common_utils
@patch('pm.cli.common_utils.get_task_by_slug')  # Target common_utils
def test_resolve_task_by_uuid(mock_get_by_slug, mock_get_by_id):
    """Test resolving task by UUID within the correct project."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    task_id = str(uuid.uuid4())
    mock_task = Task(id=task_id, project_id=mock_project_obj.id,
                     name="Test Task", slug="test-task", status=TaskStatus.NOT_STARTED)
    mock_get_by_id.return_value = mock_task

    resolved_task = resolve_task_identifier(
        mock_conn, mock_project_obj, task_id)

    mock_get_by_id.assert_called_once_with(mock_conn, task_id)
    mock_get_by_slug.assert_not_called()
    assert resolved_task == mock_task


@patch('pm.cli.common_utils.get_task')  # Target common_utils
@patch('pm.cli.common_utils.get_task_by_slug')  # Target common_utils
def test_resolve_task_by_slug(mock_get_by_slug, mock_get_by_id):
    """Test resolving task by slug within the correct project."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    task_slug = "test-task-slug"
    mock_task = Task(id=str(uuid.uuid4()), project_id=mock_project_obj.id,
                     name="Test Task", slug=task_slug, status=TaskStatus.NOT_STARTED)
    mock_get_by_id.return_value = None  # Simulate ID lookup failure/not UUID
    mock_get_by_slug.return_value = mock_task

    resolved_task = resolve_task_identifier(
        mock_conn, mock_project_obj, task_slug)

    mock_get_by_id.assert_not_called()  # Because it's not a UUID
    mock_get_by_slug.assert_called_once_with(
        mock_conn, mock_project_obj.id, task_slug)
    assert resolved_task == mock_task


@patch('pm.cli.common_utils.get_task')  # Target common_utils
@patch('pm.cli.common_utils.get_task_by_slug')  # Target common_utils
def test_resolve_task_uuid_wrong_project(mock_get_by_slug, mock_get_by_id):
    """Test resolving task by UUID when it belongs to a different project."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    task_id = str(uuid.uuid4())
    wrong_project_id = str(uuid.uuid4())
    mock_task_wrong_proj = Task(id=task_id, project_id=wrong_project_id,
                                name="Test Task", slug="test-task", status=TaskStatus.NOT_STARTED)
    # Simulate finding the task by ID
    mock_get_by_id.return_value = mock_task_wrong_proj
    # Ensure slug lookup also fails for this UUID
    mock_get_by_slug.return_value = None

    with pytest.raises(click.UsageError, match=f"Task not found with identifier '{task_id}' in project '{mock_project_obj.name}'"):
        resolve_task_identifier(mock_conn, mock_project_obj, task_id)

    mock_get_by_id.assert_called_once_with(mock_conn, task_id)
    # It should try slug lookup after ID check fails due to wrong project
    mock_get_by_slug.assert_called_once_with(
        mock_conn, mock_project_obj.id, task_id)


@patch('pm.cli.common_utils.get_task')  # Target common_utils
@patch('pm.cli.common_utils.get_task_by_slug')  # Target common_utils
def test_resolve_task_slug_wrong_project(mock_get_by_slug, mock_get_by_id):
    """Test resolving task by slug when slug exists but in different project."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    task_slug = "shared-slug"
    # Simulate get_task_by_slug returning None for the *correct* project
    mock_get_by_slug.return_value = None
    mock_get_by_id.return_value = None  # Not a UUID

    with pytest.raises(click.UsageError, match=f"Task not found with identifier '{task_slug}' in project '{mock_project_obj.name}'"):
        resolve_task_identifier(mock_conn, mock_project_obj, task_slug)

    mock_get_by_id.assert_not_called()
    mock_get_by_slug.assert_called_once_with(
        mock_conn, mock_project_obj.id, task_slug)


@patch('pm.cli.common_utils.get_task')  # Target common_utils
@patch('pm.cli.common_utils.get_task_by_slug')  # Target common_utils
def test_resolve_task_not_found(mock_get_by_slug, mock_get_by_id):
    """Test resolving non-existent task identifier."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    identifier = "non-existent-task"
    mock_get_by_id.return_value = None
    mock_get_by_slug.return_value = None

    with pytest.raises(click.UsageError, match=f"Task not found with identifier '{identifier}' in project '{mock_project_obj.name}'"):
        resolve_task_identifier(mock_conn, mock_project_obj, identifier)

    mock_get_by_id.assert_not_called()
    mock_get_by_slug.assert_called_once_with(
        mock_conn, mock_project_obj.id, identifier)
