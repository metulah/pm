"""Project model for the PM tool."""

import datetime
from dataclasses import dataclass
from typing import Optional
from ..core.types import ProjectStatus  # Import the new enum


@dataclass
class Project:
    """A project that contains tasks and notes."""
    id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE  # Add status field with default
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    def validate(self):
        """Validate project data."""
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Project name cannot exceed 100 characters")
