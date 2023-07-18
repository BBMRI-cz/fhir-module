"""Main module"""
import logging
import os
import time

import schedule

from persistence.condition_xml_repository import ConditionXMLRepository
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService
from util.custom_logger import setup_logger

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    blaze_service = BlazeService(patient_service=PatientService(SampleDonorXMLFilesRepository()),
                                 condition_service=ConditionService(ConditionXMLRepository()),
                                 blaze_url=os.getenv("BLAZE_URL", "http://localhost:8080/fhir"))
    logger.info("Successfully started FHIR_Module!")
    if blaze_service.get_num_of_patients() == 0:
        logger.info("Starting upload of patients...")
        blaze_service.initial_upload_of_all_patients()
        logger.info('Number of patients successfully uploaded: %s',
                    blaze_service.get_num_of_patients())
        logger.info("Starting upload of conditions...")
        blaze_service.sync_conditions()
    else:
        logger.debug("Patients already present in the FHIR store.")
        schedule.every().day.do(blaze_service.sync_patients)
        schedule.every().day.do(blaze_service.sync_conditions())
    while True:
        schedule.run_pending()
        time.sleep(1)
