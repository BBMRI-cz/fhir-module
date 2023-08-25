import abc
from typing import Generator

from model.sample_collection import SampleCollection


class SampleCollectionRepository:
    @abc.abstractmethod
    def get_all(self) -> Generator[SampleCollection, None, None]:
        """Get all conditions."""
