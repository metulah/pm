"""Note model for the PM tool."""

import uuid
import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Note:
    """A note associated with a project or task."""
    id: str
    content: str
    entity_type: str  # "task" or "project"
    entity_id: str  # ID of the task or project
    author: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        """Validate note data."""
        if not self.content:
            raise ValueError("Note content cannot be empty")
        if self.entity_type not in ["task", "project"]:
            raise ValueError("Entity type must be 'task' or 'project'")
        if not self.entity_id:
            raise ValueError("Entity ID cannot be empty")

    @classmethod
    def from_dict(cls, data: dict):
        """Create a Note instance from a dictionary."""
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
        """Convert the note to a dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
