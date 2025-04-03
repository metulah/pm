import uuid
import datetime
import enum
import json
from typing import Optional, List, Any
from dataclasses import dataclass


class TaskStatus(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


@dataclass
class Project:
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Project name cannot exceed 100 characters")


@dataclass
class Task:
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        if not self.name:
            raise ValueError("Task name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Task name cannot exceed 100 characters")
        if not self.project_id:
            raise ValueError("Task must be associated with a project")

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            project_id=data['project_id'],
            name=data['name'],
            description=data.get('description'),
            status=TaskStatus(
                data['status']) if 'status' in data else TaskStatus.NOT_STARTED,
            created_at=datetime.datetime.fromisoformat(
                data['created_at']) if 'created_at' in data else datetime.datetime.now(),
            updated_at=datetime.datetime.fromisoformat(
                data['updated_at']) if 'updated_at' in data else datetime.datetime.now()
        )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Subtask:
    id: str
    task_id: str
    name: str
    description: Optional[str] = None
    required_for_completion: bool = True
    status: TaskStatus = TaskStatus.NOT_STARTED
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        if not self.name:
            raise ValueError("Subtask name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Subtask name cannot exceed 100 characters")
        if not self.task_id:
            raise ValueError("Subtask must be associated with a task")

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            task_id=data['task_id'],
            name=data['name'],
            description=data.get('description'),
            required_for_completion=data.get('required_for_completion', True),
            status=TaskStatus(
                data['status']) if 'status' in data else TaskStatus.NOT_STARTED,
            created_at=datetime.datetime.fromisoformat(
                data['created_at']) if 'created_at' in data else datetime.datetime.now(),
            updated_at=datetime.datetime.fromisoformat(
                data['updated_at']) if 'updated_at' in data else datetime.datetime.now()
        )

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'required_for_completion': self.required_for_completion,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


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
            metadata.value_datetime = value if isinstance(
                value, datetime.datetime) else datetime.datetime.fromisoformat(value)
        elif metadata.value_type == "bool":
            metadata.value_bool = bool(value)
        elif metadata.value_type == "json":
            metadata.value_json = json.dumps(
                value) if not isinstance(value, str) else value

        return metadata


@dataclass
class Note:
    id: str
    content: str
    entity_type: str  # "task" or "project"
    entity_id: str  # ID of the task or project
    author: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        if not self.content:
            raise ValueError("Note content cannot be empty")
        if self.entity_type not in ["task", "project"]:
            raise ValueError("Entity type must be 'task' or 'project'")
        if not self.entity_id:
            raise ValueError("Entity ID cannot be empty")

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            content=data['content'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            author=data.get('author'),
            created_at=datetime.datetime.fromisoformat(
                data['created_at']) if 'created_at' in data else datetime.datetime.now(),
            updated_at=datetime.datetime.fromisoformat(
                data['updated_at']) if 'updated_at' in data else datetime.datetime.now()
        )

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class TaskTemplate:
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        if not self.name:
            raise ValueError("Template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Template name cannot exceed 100 characters")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SubtaskTemplate:
    id: str
    template_id: str
    name: str
    description: Optional[str] = None
    required_for_completion: bool = True

    def validate(self):
        if not self.name:
            raise ValueError("Subtask template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError(
                "Subtask template name cannot exceed 100 characters")
        if not self.template_id:
            raise ValueError(
                "Subtask template must be associated with a task template")

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'required_for_completion': self.required_for_completion
        }
