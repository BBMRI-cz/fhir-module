import abc

from persistence.biobank_repository import BiobankRepository
from persistence.condition_repository import ConditionRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.sample_repository import SampleRepository


class RepositoryFactory(abc.ABC):
    """Abstract class Representing factory for instantiating repositories, regardless of their concrete type"""
    @abc.abstractmethod
    def create_condition_repository(self) -> ConditionRepository:
        pass

    @abc.abstractmethod
    def create_sample_collection_repository(self, miabis_on_fhir_model: bool = False) -> SampleCollectionRepository:
        pass

    @abc.abstractmethod
    def create_sample_repository(self, miabis_on_fhir_model: bool = False) -> SampleRepository:
        pass

    @abc.abstractmethod
    def create_sample_donor_repository(self, miabis_on_fhir_model: bool = False) -> SampleDonorRepository:
        pass

    @abc.abstractmethod
    def create_biobank_repository(self) -> BiobankRepository:
        pass
