"""Main module"""
import logging
import sys
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import BLAZE_URL
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available
from persistence.factories.factory_util import get_repository_factory

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting FHIR_Module...")
    if is_endpoint_available(endpoint_url=BLAZE_URL, wait_time=10, max_attempts=5):
        repository_factory = get_repository_factory()
        patient_service = PatientService(repository_factory.create_sample_donor_repository())
        condition_service = ConditionService(repository_factory.create_condition_repository())
        sample_service = SampleService(repository_factory.create_sample_repository())
        sample_collection_repository = repository_factory.create_sample_collection_repository()
        blaze_service = BlazeService(patient_service=patient_service, condition_service=condition_service,
                                     sample_service=sample_service, blaze_url=BLAZE_URL,
                                     sample_collection_repository=sample_collection_repository)
        blaze_service.sync_samples()
        blaze_service.sync()
    else:
        logger.error("Exiting FHIR_Module.")
        sys.exit()
