"""Module for handling Sample persistence."""
import abc
from typing import List

from model.sample import Sample


class SampleRepository:
    """Class for interacting with Sample storage"""

    @abc.abstractmethod
    def get_all(self) -> List[Sample]:
        """Get all conditions."""
