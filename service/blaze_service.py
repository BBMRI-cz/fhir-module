import logging
import os

import requests

from model.sample_donor import SampleDonor
from service.patient_service import PatientService

logger = logging.getLogger(__name__)


class BlazeService:
    """Blaze url must without a trailing /"""

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

    def get_num_of_patients(self):
        try:
            return requests.get(url=self._blaze_url + "/Patient?_summary=count").json().get("total")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 0

    def is_present_in_blaze(self, identifier: str) -> bool:
        try:
            return requests.get(url=self._blaze_url + "/Patient?identifier=" + identifier + "&_summary=count")\
                .json()\
                .get(
                "total") > 0
        except TypeError:
            return False

    def sync_patients(self):
        for donor in self._patient_service.get_all():
            if not self.is_present_in_blaze(donor.identifier):
                try:
                    self.__upload_donor(donor)
                except requests.exceptions.ConnectionError:
                    logger.error("Cannot connect to blaze!")
                    return

    def __upload_donor(self, donor: SampleDonor) -> int:
        res = requests.post(url=self._blaze_url + "/Patient", json=donor.to_fhir().as_json())
        logger.info("Patient " + donor.identifier + "uploaded")
        return res.status_code
