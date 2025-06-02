"""Storage layer for the PM tool."""

from .db import init_db
from .project import (
    # Add get_project_by_slug
    create_project, get_project, get_project_by_slug, update_project,
    delete_project, list_projects, ProjectNotEmptyError
)
from .task import (
    create_task, get_task, update_task, delete_task,
    list_tasks, add_task_dependency, remove_task_dependency,
    get_task_dependencies, has_circular_dependency
)
from .metadata import (
    create_task_metadata, get_task_metadata,
    get_task_metadata_value, update_task_metadata,
    delete_task_metadata, query_tasks_by_metadata
)
from .note import (
    create_note, get_note, update_note,
    delete_note, list_notes
)
from .subtask import (
    create_subtask, get_subtask, update_subtask,
    delete_subtask, list_subtasks
)
from .template import (
    create_task_template, get_task_template,
    update_task_template, delete_task_template,
    list_task_templates, create_subtask_template,
    get_subtask_template, update_subtask_template,
    delete_subtask_template, list_subtask_templates,
    apply_template_to_task
)

__all__ = [
    'init_db',
    # Project operations
    # Add get_project_by_slug
    'create_project', 'get_project', 'get_project_by_slug', 'update_project',
    'delete_project', 'list_projects', 'ProjectNotEmptyError',
    # Task operations
    'create_task', 'get_task', 'update_task', 'delete_task',
    'list_tasks', 'add_task_dependency', 'remove_task_dependency',
    'get_task_dependencies', 'has_circular_dependency',
    # Metadata operations
    'create_task_metadata', 'get_task_metadata',
    'get_task_metadata_value', 'update_task_metadata',
    'delete_task_metadata', 'query_tasks_by_metadata',
    # Note operations
    'create_note', 'get_note', 'update_note',
    'delete_note', 'list_notes',
    # Subtask operations
    'create_subtask', 'get_subtask', 'update_subtask',
    'delete_subtask', 'list_subtasks',
    # Template operations
    'create_task_template', 'get_task_template',
    'update_task_template', 'delete_task_template',
    'list_task_templates', 'create_subtask_template',
    'get_subtask_template', 'update_subtask_template',
    'delete_subtask_template', 'list_subtask_templates',
    'apply_template_to_task'
]
