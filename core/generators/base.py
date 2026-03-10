"""
Base class and UseCase dataclass shared by all generators.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type


class BaseGenerator(ABC):
    """All industry generators must implement generate()."""

    @abstractmethod
    def generate(self) -> dict:
        ...


@dataclass
class UseCase:
    """Describes a streamable data scenario."""
    id:              str
    title:           str
    description:     str
    schema_preview:  str          # short human-readable schema hint shown on the card
    generator_class: Type[BaseGenerator]  # instantiated when streaming starts
