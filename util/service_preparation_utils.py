from dataclasses import dataclass

from persistence.factories.factory_util import get_repository_factory
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.biobank_repository import BiobankRepository
from service.patient_service import PatientService
from service.condition_service import ConditionService
from service.sample_service import SampleService

@dataclass
class ServiceBundle:
    patient_service: PatientService
    condition_service: ConditionService
    sample_service: SampleService
    sample_collection_repository: SampleCollectionRepository


@dataclass
class MiabisServiceBundle:
    patient_service: PatientService
    sample_service: SampleService
    sample_collection_repository: SampleCollectionRepository
    biobank_repository: BiobankRepository


def prepare_services() -> ServiceBundle:
    repository_factory = get_repository_factory()
    
    patient_service = PatientService(repository_factory.create_sample_donor_repository())
    condition_service = ConditionService(repository_factory.create_condition_repository())
    sample_service = SampleService(repository_factory.create_sample_repository())
    sample_collection_repository = repository_factory.create_sample_collection_repository()
    
    return ServiceBundle(
        patient_service=patient_service,
        condition_service=condition_service,
        sample_service=sample_service,
        sample_collection_repository=sample_collection_repository
    )


def prepare_services_miabis() -> MiabisServiceBundle:
    repository_factory = get_repository_factory()
    
    patient_service = PatientService(repository_factory.create_sample_donor_repository(True))
    sample_service = SampleService(repository_factory.create_sample_repository(True))
    sample_collection_repository = repository_factory.create_sample_collection_repository(True)
    biobank_repository = repository_factory.create_biobank_repository()
    
    return MiabisServiceBundle(
        patient_service=patient_service,
        sample_service=sample_service,
        sample_collection_repository=sample_collection_repository,
        biobank_repository=biobank_repository
    )