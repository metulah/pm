# Implementation Plan: Add Metadata Support to Tasks

## Overview

This plan outlines the implementation of a flexible metadata system for tasks in the PM tool. The metadata system will support multiple data types and efficient querying capabilities.

## Database Schema

We'll add a new `task_metadata` table with the following structure:

```sql
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
```

## Implementation Steps

### 1. Update Models

Add a new `TaskMetadata` class to `models.py`:

```python
@dataclass
class TaskMetadata:
    task_id: str
    key: str
    value_type: str  # "string", "int", "float", "datetime", "bool", "json"
    value_string: Optional[str] = None
    value_int: Optional[int] = None
    value_float: Optional[float] = None
    value_datetime: Optional[datetime.datetime] = None
    value_bool: Optional[bool] = None
    value_json: Optional[str] = None  # JSON stored as string

    def get_value(self):
        """Get the value based on the value_type."""
        if self.value_type == "string":
            return self.value_string
        elif self.value_type == "int":
            return self.value_int
        elif self.value_type == "float":
            return self.value_float
        elif self.value_type == "datetime":
            return self.value_datetime
        elif self.value_type == "bool":
            return self.value_bool
        elif self.value_type == "json":
            return json.loads(self.value_json) if self.value_json else None
        return None

    @classmethod
    def create(cls, task_id: str, key: str, value, value_type: Optional[str] = None):
        """Create a TaskMetadata instance with the appropriate value field set."""
        metadata = cls(task_id=task_id, key=key, value_type="string")

        if value_type:
            metadata.value_type = value_type
        else:
            # Auto-detect type
            if isinstance(value, str):
                metadata.value_type = "string"
            elif isinstance(value, int):
                metadata.value_type = "int"
            elif isinstance(value, float):
                metadata.value_type = "float"
            elif isinstance(value, datetime.datetime):
                metadata.value_type = "datetime"
            elif isinstance(value, bool):
                metadata.value_type = "bool"
            elif isinstance(value, (dict, list)):
                metadata.value_type = "json"

        # Set the appropriate value field
        if metadata.value_type == "string":
            metadata.value_string = str(value)
        elif metadata.value_type == "int":
            metadata.value_int = int(value)
        elif metadata.value_type == "float":
            metadata.value_float = float(value)
        elif metadata.value_type == "datetime":
            metadata.value_datetime = value if isinstance(value, datetime.datetime) else datetime.datetime.fromisoformat(value)
        elif metadata.value_type == "bool":
            metadata.value_bool = bool(value)
        elif metadata.value_type == "json":
            metadata.value_json = json.dumps(value) if not isinstance(value, str) else value

        return metadata
```

Update the `Task` class to include metadata-related methods:

```python
def to_dict(self):
    result = {
        'id': self.id,
        'project_id': self.project_id,
        'name': self.name,
        'description': self.description,
        'status': self.status.value,
        'created_at': self.created_at.isoformat(),
        'updated_at': self.updated_at.isoformat()
    }
    return result
```

### 2. Update Storage

Add the following functions to `storage.py`:

```python
def init_db(db_path: str = "pm.db") -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    # Existing code...

    with conn:
        # Existing tables...

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

    return conn

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

def query_tasks_by_metadata(conn: sqlite3.Connection, key: str, value, value_type: Optional[str] = None) -> List[Task]:
    """Query tasks by metadata."""
    metadata = TaskMetadata.create(task_id="", key=key, value=value, value_type=value_type)

    # Determine which column to query based on value_type
    value_column = f"value_{metadata.value_type}"
    value_param = getattr(metadata, value_column)

    query = f"""
    SELECT t.* FROM tasks t
    JOIN task_metadata tm ON t.id = tm.task_id
    WHERE tm.key = ? AND tm.value_type = ? AND tm.{value_column} = ?
    """

    rows = conn.execute(query, (key, metadata.value_type, value_param)).fetchall()
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
```

### 3. Update CLI

Add a new command group for metadata in `cli.py`:

```python
@task.group()
def metadata():
    """Manage task metadata."""
    pass

@metadata.command("set")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
def metadata_set(task_id, key, value, value_type):
    """Set metadata for a task."""
    conn = get_db_connection()
    try:
        # Convert value based on type
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "datetime":
            value = datetime.fromisoformat(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "yes", "1")
        elif value_type == "json":
            value = json.loads(value)

        metadata = update_task_metadata(conn, task_id, key, value, value_type)
        if metadata:
            click.echo(json_response("success", {"task_id": metadata.task_id, "key": metadata.key, "value": metadata.get_value()}))
        else:
            click.echo(json_response("error", message=f"Task {task_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

@metadata.command("get")
@click.argument("task_id")
@click.option("--key", help="Metadata key (optional)")
def metadata_get(task_id, key):
    """Get metadata for a task."""
    conn = get_db_connection()
    try:
        metadata_list = get_task_metadata(conn, task_id, key)
        result = [{"key": m.key, "value": m.get_value(), "type": m.value_type} for m in metadata_list]
        click.echo(json_response("success", result))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

@metadata.command("delete")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
def metadata_delete(task_id, key):
    """Delete metadata for a task."""
    conn = get_db_connection()
    try:
        success = delete_task_metadata(conn, task_id, key)
        if success:
            click.echo(json_response("success", message=f"Metadata '{key}' deleted from task {task_id}"))
        else:
            click.echo(json_response("error", message=f"Metadata '{key}' not found for task {task_id}"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

@metadata.command("query")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
def metadata_query(key, value, value_type):
    """Query tasks by metadata."""
    conn = get_db_connection()
    try:
        # Convert value based on type
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "datetime":
            value = datetime.fromisoformat(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "yes", "1")
        elif value_type == "json":
            value = json.loads(value)

        tasks = query_tasks_by_metadata(conn, key, value, value_type)
        click.echo(json_response("success", [t.__dict__ for t in tasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()
```

### 4. Testing

We'll need to test the following scenarios:

1. Creating metadata with different data types
2. Retrieving metadata
3. Updating metadata
4. Deleting metadata
5. Querying tasks by metadata
6. Error handling (e.g., invalid task ID, invalid value type)

### 5. Documentation

Update the PM tool documentation to include information about the new metadata functionality.

## Implementation Timeline

1. Update models.py (1 hour)
2. Update storage.py (2 hours)
3. Update cli.py (1 hour)
4. Testing (2 hours)
5. Documentation (1 hour)

Total estimated time: 7 hours

## Usage Examples

```bash
# Set metadata
python -m pm.cli task metadata set <task_id> --key priority --value high

# Set metadata with explicit type
python -m pm.cli task metadata set <task_id> --key due_date --value "2025-05-01T12:00:00" --type datetime

# Get all metadata for a task
python -m pm.cli task metadata get <task_id>

# Get specific metadata
python -m pm.cli task metadata get <task_id> --key priority

# Delete metadata
python -m pm.cli task metadata delete <task_id> --key priority

# Query tasks by metadata
python -m pm.cli task metadata query --key priority --value high
```
