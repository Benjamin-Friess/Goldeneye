"""Domain model: a trading strategy definition."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Strategy:
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
