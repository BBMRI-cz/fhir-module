import abc
from typing import Generator

from model.interface.collection_interface import CollectionInterface


class SampleCollectionRepository:
    @abc.abstractmethod
    def get_all(self) -> Generator[CollectionInterface, None, None]:
        """Get all conditions."""
