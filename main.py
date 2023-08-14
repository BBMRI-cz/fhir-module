"""Main module"""
import logging
import sys

from persistence.condition_xml_repository import ConditionXMLRepository
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from persistence.sample_xml_repository import SampleXMLRepository
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import BLAZE_URL, RECORDS_DIR_PATH, PARSING_MAP
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting FHIR_Module...")
    if is_endpoint_available(endpoint_url=BLAZE_URL, wait_time=10, max_attempts=5):
        blaze_service = BlazeService(patient_service=PatientService(
            SampleDonorXMLFilesRepository(records_path=RECORDS_DIR_PATH,
                                          donor_parsing_map=PARSING_MAP['donor_map'])),
                                     condition_service=ConditionService(
                                         ConditionXMLRepository(records_path=RECORDS_DIR_PATH,
                                                                condition_parsing_map=PARSING_MAP['condition_map'])),
                                     sample_service=SampleService(SampleXMLRepository(records_path=RECORDS_DIR_PATH,
                                                                                      sample_parsing_map=
                                                                                      PARSING_MAP['sample_map'])),
                                     blaze_url=BLAZE_URL)
        blaze_service.sync()
    else:
        logger.error("Exiting FHIR_Module.")
        sys.exit()
