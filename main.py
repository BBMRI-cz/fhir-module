import os
import time

import schedule

from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService

if __name__ == "__main__":
    blaze_service = BlazeService(PatientService(SampleDonorXMLFilesRepository()),
                                 os.getenv("BLAZE_URL", "http://localhost:8080/fhir/"))
    schedule.every().day.at("10:00").do(blaze_service.initial_upload_of_all_patients)
    while True:
        schedule.run_pending()
        time.sleep(1)
