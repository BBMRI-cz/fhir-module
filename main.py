import os
import time
import logging
import logging.config


import requests
import schedule
import yaml

from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService


def setup_logger():
    with open('logging.yaml', 'r') as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)


if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    res = requests.get(url="http://localhost:8080/fhir/Patient?_summary=count")
    blaze_service = BlazeService(PatientService(SampleDonorXMLFilesRepository()),
                                 os.getenv("BLAZE_URL", "http://localhost:8080/fhir/"))
    if res.text.find("total") == 0:
        blaze_service.initial_upload_of_all_patients()
    else:
        logger.debug("Patients already present in the FHIR store.")
    while True:
        schedule.run_pending()
        time.sleep(1)
