"""Project model for the PM tool."""

import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    """A project that contains tasks and notes."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        """Validate project data."""
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Project name cannot exceed 100 characters")
