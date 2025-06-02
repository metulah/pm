"""Task metadata model for the PM tool."""

import json
import datetime
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class TaskMetadata:
    """Metadata associated with a task."""
    task_id: str
    key: str
    value_type: str  # "string", "int", "float", "datetime", "bool", "json"
    value_string: Optional[str] = None
    value_int: Optional[int] = None
    value_float: Optional[float] = None
    value_datetime: Optional[datetime.datetime] = None
    value_bool: Optional[bool] = None
    value_json: Optional[str] = None  # JSON stored as string

    def get_value(self) -> Any:
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
    def create(cls, task_id: str, key: str, value: Any, value_type: Optional[str] = None):
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
