"""Subtask model for the PM tool."""

import uuid
import datetime
from dataclasses import dataclass
from typing import Optional

from ..core.types import TaskStatus


@dataclass
class Subtask:
    """A subtask within a task."""
    id: str
    task_id: str
    name: str
    description: Optional[str] = None
    required_for_completion: bool = True
    status: TaskStatus = TaskStatus.NOT_STARTED
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        """Validate subtask data."""
        if not self.name:
            raise ValueError("Subtask name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Subtask name cannot exceed 100 characters")
        if not self.task_id:
            raise ValueError("Subtask must be associated with a task")

    @classmethod
    def from_dict(cls, data: dict):
        """Create a Subtask instance from a dictionary."""
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
        """Convert the subtask to a dictionary."""
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
