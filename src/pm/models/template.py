"""Template models for the PM tool."""

import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskTemplate:
    """A template for creating tasks with predefined subtasks."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        """Validate template data."""
        if not self.name:
            raise ValueError("Template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Template name cannot exceed 100 characters")

    def to_dict(self):
        """Convert the template to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SubtaskTemplate:
    """A template for creating subtasks within a task template."""
    id: str
    template_id: str
    name: str
    description: Optional[str] = None
    required_for_completion: bool = True

    def validate(self):
        """Validate subtask template data."""
        if not self.name:
            raise ValueError("Subtask template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError(
                "Subtask template name cannot exceed 100 characters")
        if not self.template_id:
            raise ValueError(
                "Subtask template must be associated with a task template")

    def to_dict(self):
        """Convert the subtask template to a dictionary."""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'required_for_completion': self.required_for_completion
        }
