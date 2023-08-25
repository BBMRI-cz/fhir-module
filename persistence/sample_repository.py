"""Module for handling Sample persistence."""
import abc
from typing import Generator

from model.sample import Sample


class SampleRepository:
    """Class for interacting with Sample storage"""

    @abc.abstractmethod
    def get_all(self) -> Generator[Sample, None, None]:
        """Get all conditions."""
