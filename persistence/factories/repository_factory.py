import abc

from persistence.condition_repository import ConditionRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.sample_repository import SampleRepository


class RepositoryFactory(abc.ABC):
    @abc.abstractmethod
    def create_condition_repository(self) -> ConditionRepository:
        pass

    @abc.abstractmethod
    def create_sample_collection_repository(self) -> SampleCollectionRepository:
        pass

    @abc.abstractmethod
    def create_sample_repository(self) -> SampleRepository:
        pass

    @abc.abstractmethod
    def create_sample_donor_repository(self) -> SampleDonorRepository:
        pass
