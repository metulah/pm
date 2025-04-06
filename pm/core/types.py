"""Core types and enums used throughout the PM tool."""

import enum


class TaskStatus(enum.Enum):
    """Status values for tasks and subtasks."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class ProjectStatus(enum.Enum):
    """Status values for projects."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    PROSPECTIVE = "PROSPECTIVE"
    CANCELLED = "CANCELLED"
