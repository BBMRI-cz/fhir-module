import abc
from typing import Generator

from model.interface.collection_interface import CollectionInterface
from model.sample_collection import SampleCollection


class SampleCollectionRepository:
    @abc.abstractmethod
    def get_all(self) -> Generator[CollectionInterface, None, None]:
        """Get all conditions."""
