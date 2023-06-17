import logging
import os
import time



import requests
import schedule
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService
from util.custom_logger import setup_logger

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    res = requests.get(url="http://localhost:8080/fhir/Patient?_summary=count")
    blaze_service = BlazeService(PatientService(SampleDonorXMLFilesRepository()),
                                 os.getenv("BLAZE_URL", "http://localhost:8080/fhir"))
    if res.json().get("total") == 0:
        blaze_service.initial_upload_of_all_patients()
    else:
        blaze_service.sync_patients()
        logger.debug("Patients already present in the FHIR store.")
        schedule.every().day.do(blaze_service.sync_patients)
    while True:
        schedule.run_pending()
        time.sleep(1)