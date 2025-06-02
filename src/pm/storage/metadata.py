"""Task metadata storage operations."""

import sqlite3
from typing import Optional, List, Any

from ..models import Task, TaskMetadata, TaskStatus


def create_task_metadata(conn: sqlite3.Connection, metadata: TaskMetadata) -> TaskMetadata:
    """Create a new task metadata entry."""
    with conn:
        conn.execute(
            """INSERT INTO task_metadata (
                task_id, key, value_type, value_string, value_int,
                value_float, value_datetime, value_bool, value_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (metadata.task_id, metadata.key, metadata.value_type,
             metadata.value_string, metadata.value_int,
             metadata.value_float, metadata.value_datetime,
             metadata.value_bool, metadata.value_json)
        )
    return metadata


def get_task_metadata(conn: sqlite3.Connection, task_id: str, key: Optional[str] = None) -> List[TaskMetadata]:
    """Get metadata for a task."""
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


def update_task_metadata(conn: sqlite3.Connection, task_id: str, key: str, value: Any, value_type: Optional[str] = None) -> Optional[TaskMetadata]:
    """Update or create task metadata."""
    metadata = TaskMetadata.create(task_id, key, value, value_type)

    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO task_metadata (
                task_id, key, value_type, value_string, value_int,
                value_float, value_datetime, value_bool, value_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (metadata.task_id, metadata.key, metadata.value_type,
             metadata.value_string, metadata.value_int,
             metadata.value_float, metadata.value_datetime,
             metadata.value_bool, metadata.value_json)
        )
    return metadata


def delete_task_metadata(conn: sqlite3.Connection, task_id: str, key: str) -> bool:
    """Delete metadata for a task."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM task_metadata WHERE task_id = ? AND key = ?",
            (task_id, key)
        )
    return cursor.rowcount > 0


def query_tasks_by_metadata(conn: sqlite3.Connection, key: str, value: Any, value_type: Optional[str] = None) -> List[Task]:
    """Query tasks by metadata value."""

    try:
        # Create a temporary metadata object to get the correct value field
        metadata = TaskMetadata.create(
            task_id="", key=key, value=value, value_type=value_type)
        value_type = metadata.value_type
        value_column = f"value_{value_type}"
        value_to_compare = getattr(metadata, value_column)

        # Debug: Check if there are any tasks in the database
        all_tasks = conn.execute("SELECT id, name FROM tasks").fetchall()
        if not all_tasks:
            print("No tasks found in the database")
        else:
            print(f"Found {len(all_tasks)} tasks in the database")
            for task in all_tasks:
                print(f"Task: {task['id']}, {task['name']}")

        # Debug: Check if there are any metadata entries in the database
        all_metadata = conn.execute(
            "SELECT task_id, key, value_type, value_string FROM task_metadata").fetchall()
        if not all_metadata:
            print("No metadata found in the database")
        else:
            print(
                f"Found {len(all_metadata)} metadata entries in the database")
            for meta in all_metadata:
                print(
                    f"Metadata: task_id={meta['task_id']}, key={meta['key']}, value_type={meta['value_type']}, value_string={meta['value_string']}")

        # Build the query based on the value type
        if value_type == "string":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_string = ?
            ORDER BY t.name
            """
        elif value_type == "int":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_int = ?
            ORDER BY t.name
            """
        elif value_type == "float":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_float = ?
            ORDER BY t.name
            """
        elif value_type == "datetime":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_datetime = ?
            ORDER BY t.name
            """
        elif value_type == "bool":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_bool = ?
            ORDER BY t.name
            """
        elif value_type == "json":
            query = """
            SELECT DISTINCT t.id, t.project_id, t.name, t.description, t.status,
                   t.created_at, t.updated_at
            FROM tasks t
            JOIN task_metadata m ON t.id = m.task_id
            WHERE m.key = ? AND m.value_json = ?
            ORDER BY t.name
            """
        else:
            raise ValueError(f"Unsupported value type: {value_type}")

        print(f"Executing query: {query}")
        print(
            f"Query parameters: key={key}, value_to_compare={value_to_compare}")

        rows = conn.execute(query, (key, value_to_compare)).fetchall()

        print(f"Query returned {len(rows)} rows")

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
    except Exception as e:
        print(f"Error in query_tasks_by_metadata: {e}")
        print(
            f"Query parameters: key={key}, value={value}, value_type={value_type}")
        print(
            f"Value column: {value_column}, value_to_compare: {value_to_compare}")
        raise
