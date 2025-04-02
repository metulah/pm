import uuid
import datetime
import enum
from typing import Optional, List
from dataclasses import dataclass


class TaskStatus(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
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
