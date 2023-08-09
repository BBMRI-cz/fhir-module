"""Main module"""
import logging
import sys

from persistence.condition_xml_repository import ConditionXMLRepository
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService
from util.config import BLAZE_URL
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting FHIR_Module...")
    if is_endpoint_available(endpoint_url=BLAZE_URL, wait_time=10, max_attempts=5):
        blaze_service = BlazeService(patient_service=PatientService(SampleDonorXMLFilesRepository()),
                                     condition_service=ConditionService(ConditionXMLRepository()),
                                     blaze_url=BLAZE_URL)
        blaze_service.sync()
    else:
        logger.error("Exiting FHIR_Module")
        sys.exit()
