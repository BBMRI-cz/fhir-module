"""Module for handling condition persistence"""
import abc
from typing import Generator

from model.condition import Condition


class ConditionRepository(abc.ABC):
    """Class for handling Condition persistence"""

    @abc.abstractmethod
    def get_all(self) -> Generator[Condition, None, None]:
        """Get all conditions."""
