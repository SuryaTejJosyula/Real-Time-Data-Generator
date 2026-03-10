"""
Base class and UseCase dataclass shared by all generators.
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type


class BaseGenerator(ABC):
    """All industry generators must implement _generate_normal()."""

    def __init__(self):
        self.anomaly_mode: bool = False

    def generate(self) -> dict:
        """Route: 30% chance of anomaly when anomaly_mode is enabled."""
        if self.anomaly_mode and random.random() < 0.30:
            return self.inject_anomaly()
        return self._generate_normal()

    @abstractmethod
    def _generate_normal(self) -> dict:
        ...

    def inject_anomaly(self) -> dict:
        """Override in subclasses for domain-specific anomalies."""
        evt = self._generate_normal()
        evt["_anomaly"] = True
        evt["_anomaly_type"] = "generic_override"
        return evt


@dataclass
class UseCase:
    """Describes a streamable data scenario."""
    id:              str
    title:           str
    description:     str
    schema_preview:  str          # short human-readable schema hint shown on the card
    generator_class: Type[BaseGenerator]  # instantiated when streaming starts
