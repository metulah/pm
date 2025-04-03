import sqlite3
import uuid
import datetime
import json
from typing import Optional, List, Any
from .models import Project, Task, TaskStatus, TaskMetadata, Note


def adapt_datetime(dt):
    """Adapt datetime.datetime to ISO 8601 date string."""
    return dt.isoformat()


def convert_datetime(ts):
    """Convert ISO 8601 datetime string to datetime.datetime."""
    return datetime.datetime.fromisoformat(ts.decode())


# Register the adapter and converter
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


def init_db(db_path: str = "pm.db") -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row

    # Create tables if they don't exist
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'NOT_STARTED',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_dependencies (
            task_id TEXT NOT NULL,
            dependency_id TEXT NOT NULL,
            PRIMARY KEY (task_id, dependency_id),
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            FOREIGN KEY (dependency_id) REFERENCES tasks (id) ON DELETE CASCADE,
            CHECK (task_id != dependency_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_metadata (
            task_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_string TEXT,
            value_int INTEGER,
            value_float REAL,
            value_datetime TIMESTAMP,
            value_bool INTEGER,
            value_json TEXT,
            PRIMARY KEY (task_id, key),
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            CHECK (value_type IN ('string', 'int', 'float', 'datetime', 'bool', 'json'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            author TEXT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (entity_type IN ('task', 'project'))
        )
        """)

    return conn


def create_project(conn: sqlite3.Connection, project: Project) -> Project:
    """Create a new project in the database."""
    project.validate()
    with conn:
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (project.id, project.name, project.description,
             project.created_at, project.updated_at)
        )
    return project


def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?",
                       (project_id,)).fetchone()
    if not row:
        return None
    return Project(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_project(conn: sqlite3.Connection, project_id: str, **kwargs) -> Optional[Project]:
    """Update a project's attributes."""
    project = get_project(conn, project_id)
    if not project:
        return None

    for key, value in kwargs.items():
        if hasattr(project, key):
            setattr(project, key, value)

    project.updated_at = datetime.datetime.now()
    project.validate()

    with conn:
        conn.execute(
            "UPDATE projects SET name = ?, description = ?, updated_at = ? WHERE id = ?",
            (project.name, project.description, project.updated_at, project.id)
        )
    return project


def delete_project(conn: sqlite3.Connection, project_id: str) -> bool:
    """Delete a project by ID."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,))
    return cursor.rowcount > 0


def list_projects(conn: sqlite3.Connection) -> List[Project]:
    """List all projects."""
    rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
    return [
        Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def create_task(conn: sqlite3.Connection, task: Task) -> Task:
    """Create a new task in the database."""
    task.validate()
    with conn:
        conn.execute(
            "INSERT INTO tasks (id, project_id, name, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.project_id, task.name, task.description,
             task.status.value, task.created_at, task.updated_at)
        )
    return task


def get_task(conn: sqlite3.Connection, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?",
                       (task_id,)).fetchone()
    if not row:
        return None
    return Task(
        id=row['id'],
        project_id=row['project_id'],
        name=row['name'],
        description=row['description'],
        status=TaskStatus(row['status']),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_task(conn: sqlite3.Connection, task_id: str, **kwargs) -> Optional[Task]:
    """Update a task's attributes."""
    task = get_task(conn, task_id)
    if not task:
        return None

    for key, value in kwargs.items():
        if hasattr(task, key):
            if key == 'status' and not isinstance(value, TaskStatus):
                value = TaskStatus(value)
            setattr(task, key, value)

    task.updated_at = datetime.datetime.now()
    task.validate()

    with conn:
        conn.execute(
            "UPDATE tasks SET project_id = ?, name = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
            (task.project_id, task.name, task.description,
             task.status.value, task.updated_at, task.id)
        )
    return task


def delete_task(conn: sqlite3.Connection, task_id: str) -> bool:
    """Delete a task by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0


def list_tasks(conn: sqlite3.Connection, project_id: Optional[str] = None, status: Optional[TaskStatus] = None) -> List[Task]:
    """List tasks with optional filtering."""
    query = "SELECT * FROM tasks"
    params = []

    if project_id or status:
        query += " WHERE"

    if project_id:
        query += " project_id = ?"
        params.append(project_id)

    if status:
        if project_id:
            query += " AND"
        query += " status = ?"
        params.append(status.value)

    query += " ORDER BY name"

    rows = conn.execute(query, params).fetchall()
    return [
        Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def add_task_dependency(conn: sqlite3.Connection, task_id: str, dependency_id: str) -> bool:
    """Add a dependency between tasks."""
    # Validate both tasks exist
    task = get_task(conn, task_id)
    dependency = get_task(conn, dependency_id)
    if not task or not dependency:
        return False

    # Prevent self-dependency
    if task_id == dependency_id:
        raise ValueError("A task cannot depend on itself")

    # Check for circular dependencies
    if has_circular_dependency(conn, dependency_id, task_id):
        raise ValueError(
            "Adding this dependency would create a circular reference")

    try:
        with conn:
            conn.execute(
                "INSERT INTO task_dependencies (task_id, dependency_id) VALUES (?, ?)",
                (task_id, dependency_id)
            )
        return True
    except sqlite3.IntegrityError:
        # Dependency already exists
        return False


def remove_task_dependency(conn: sqlite3.Connection, task_id: str, dependency_id: str) -> bool:
    """Remove a dependency between tasks."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM task_dependencies WHERE task_id = ? AND dependency_id = ?",
            (task_id, dependency_id)
        )
    return cursor.rowcount > 0


def get_task_dependencies(conn: sqlite3.Connection, task_id: str) -> List[Task]:
    """Get all dependencies for a task."""
    rows = conn.execute(
        "SELECT t.* FROM tasks t JOIN task_dependencies td ON t.id = td.dependency_id WHERE td.task_id = ?",
        (task_id,)
    ).fetchall()
    return [
        Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def has_circular_dependency(conn: sqlite3.Connection, task_id: str, potential_dependency_id: str, visited: Optional[set] = None) -> bool:
    """Check if adding a dependency would create a circular reference."""
    if visited is None:
        visited = set()

    if task_id in visited:
        return False

    visited.add(task_id)

    # If the task directly depends on the potential dependency, it would create a circle
    if task_id == potential_dependency_id:
        return True

    # Check all dependencies of the task
    for row in conn.execute(
        "SELECT dependency_id FROM task_dependencies WHERE task_id = ?",
        (task_id,)
    ):
        dependency_id = row[0]
        if has_circular_dependency(conn, dependency_id, potential_dependency_id, visited):
            return True

    return False


def create_task_metadata(conn: sqlite3.Connection, metadata: TaskMetadata) -> TaskMetadata:
    """Create a new metadata entry for a task."""
    # Check if the task exists
    task = get_task(conn, metadata.task_id)
    if not task:
        raise ValueError(f"Task {metadata.task_id} not found")

    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO task_metadata
            (task_id, key, value_type, value_string, value_int, value_float, value_datetime, value_bool, value_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.task_id,
                metadata.key,
                metadata.value_type,
                metadata.value_string,
                metadata.value_int,
                metadata.value_float,
                metadata.value_datetime,
                metadata.value_bool,
                metadata.value_json
            )
        )
    return metadata


def get_task_metadata(conn: sqlite3.Connection, task_id: str, key: Optional[str] = None) -> List[TaskMetadata]:
    """Get metadata for a task, optionally filtered by key."""
    query = "SELECT * FROM task_metadata WHERE task_id = ?"
    params = [task_id]

    if key:
        query += " AND key = ?"
        params.append(key)

    rows = conn.execute(query, params).fetchall()
    return [
        TaskMetadata(
            task_id=row['task_id'],
            key=row['key'],
            value_type=row['value_type'],
            value_string=row['value_string'],
            value_int=row['value_int'],
            value_float=row['value_float'],
            value_datetime=row['value_datetime'],
            value_bool=row['value_bool'],
            value_json=row['value_json']
        ) for row in rows
    ]


def get_task_metadata_value(conn: sqlite3.Connection, task_id: str, key: str) -> Optional[Any]:
    """Get a specific metadata value for a task."""
    metadata_list = get_task_metadata(conn, task_id, key)
    if not metadata_list:
        return None
    return metadata_list[0].get_value()


def update_task_metadata(conn: sqlite3.Connection, task_id: str, key: str, value, value_type: Optional[str] = None) -> Optional[TaskMetadata]:
    """Update metadata for a task."""
    # Check if the task exists
    task = get_task(conn, task_id)
    if not task:
        return None

    metadata = TaskMetadata.create(task_id, key, value, value_type)
    return create_task_metadata(conn, metadata)


def delete_task_metadata(conn: sqlite3.Connection, task_id: str, key: str) -> bool:
    """Delete metadata for a task."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM task_metadata WHERE task_id = ? AND key = ?",
            (task_id, key)
        )
    return cursor.rowcount > 0


def create_note(conn: sqlite3.Connection, note: Note) -> Note:
    """Create a new note in the database."""
    note.validate()
    with conn:
        conn.execute(
            "INSERT INTO notes (id, content, author, entity_type, entity_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (note.id, note.content, note.author, note.entity_type, note.entity_id,
             note.created_at, note.updated_at)
        )
    return note


def get_note(conn: sqlite3.Connection, note_id: str) -> Optional[Note]:
    """Get a note by ID."""
    row = conn.execute("SELECT * FROM notes WHERE id = ?",
                       (note_id,)).fetchone()
    if not row:
        return None
    return Note(
        id=row['id'],
        content=row['content'],
        author=row['author'],
        entity_type=row['entity_type'],
        entity_id=row['entity_id'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_note(conn: sqlite3.Connection, note_id: str, **kwargs) -> Optional[Note]:
    """Update a note's attributes."""
    note = get_note(conn, note_id)
    if not note:
        return None

    for key, value in kwargs.items():
        if hasattr(note, key):
            setattr(note, key, value)

    note.updated_at = datetime.datetime.now()
    note.validate()

    with conn:
        conn.execute(
            "UPDATE notes SET content = ?, author = ?, updated_at = ? WHERE id = ?",
            (note.content, note.author, note.updated_at, note.id)
        )
    return note


def delete_note(conn: sqlite3.Connection, note_id: str) -> bool:
    """Delete a note by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return cursor.rowcount > 0


def list_notes(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> List[Note]:
    """List notes for a task or project."""
    if entity_type not in ["task", "project"]:
        raise ValueError("Entity type must be 'task' or 'project'")

    rows = conn.execute(
        "SELECT * FROM notes WHERE entity_type = ? AND entity_id = ? ORDER BY created_at",
        (entity_type, entity_id)
    ).fetchall()
    return [
        Note(
            id=row['id'],
            content=row['content'],
            author=row['author'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def query_tasks_by_metadata(conn: sqlite3.Connection, key: str, value, value_type: Optional[str] = None) -> List[Task]:
    """Query tasks by metadata."""
    metadata = TaskMetadata.create(
        task_id="", key=key, value=value, value_type=value_type)

    # Determine which column to query based on value_type
    value_column = f"value_{metadata.value_type}"
    value_param = getattr(metadata, value_column)

    query = f"""
    SELECT t.* FROM tasks t
    JOIN task_metadata tm ON t.id = tm.task_id
    WHERE tm.key = ? AND tm.value_type = ? AND tm.{value_column} = ?
    """

    rows = conn.execute(
        query, (key, metadata.value_type, value_param)).fetchall()
    return [
        Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]
