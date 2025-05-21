"""Module for handling Sample persistence."""
import abc
from typing import Generator

from model.interface.sample_interface import SampleInterface


class SampleRepository:
    """Class for interacting with Sample storage"""

    @abc.abstractmethod
    def get_all(self) -> Generator[SampleInterface, None, None]:
        """Get all conditions."""
