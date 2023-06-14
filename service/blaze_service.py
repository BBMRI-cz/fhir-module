import logging
import os

import requests

from service.patient_service import PatientService

logger = logging.getLogger(__name__)

class BlazeService:

    def __init__(self, patient_service: PatientService, blaze_url: str):
        self._patient_service = patient_service
        self._blaze_url = blaze_url

    """This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
    patients. This method should be called only once, specifically if there are no patients in the FHIR server."""
    def initial_upload_of_all_patients(self) -> int:
        bundle = self._patient_service.get_all_patients_in_fhir_transaction()
        try:
            response = requests.post(url=self._blaze_url,
                                    json=bundle.as_json(),
                                    auth=(os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", "")))
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 404
        return response.status_code
