import os
import time

import requests
import schedule

from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService

if __name__ == "__main__":
    res = requests.get(url="http://localhost:8080/fhir/Patient?_summary=count")
    blaze_service = BlazeService(PatientService(SampleDonorXMLFilesRepository()),
                                 os.getenv("BLAZE_URL", "http://localhost:8080/fhir/"))
    if res.text.find("total") == 0:
        blaze_service.initial_upload_of_all_patients()
    else:
        print("Patients already present in the FHIR store.")
    while True:
        schedule.run_pending()
        time.sleep(1)
