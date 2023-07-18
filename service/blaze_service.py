import logging
import os

import requests
from fhirclient import client
from fhirclient.models.patient import Patient
from glom import glom

from model.condition import Condition
from model.sample_donor import SampleDonor
from service.condition_service import ConditionService
from service.patient_service import PatientService
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class BlazeService:
    def __init__(self, patient_service: PatientService, condition_service: ConditionService, blaze_url: str):
        """
        Class for interacting with a Blaze Store FHIR server
        :param patient_service:
        :param blaze_url: base url of the FHIR server. Must be without a trailing /
        """
        self._patient_service = patient_service
        self._condition_service = condition_service
        self._blaze_url = blaze_url
        self._credentials = (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))

    def initial_upload_of_all_patients(self) -> int:
        """
        This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
        patients. This method should be called only once, specifically if there are no patients in the FHIR server.
        :return: status code
        """
        bundle = self._patient_service.get_all_patients_in_fhir_transaction()
        try:
            response = requests.post(url=self._blaze_url,
                                     json=bundle.as_json(),
                                     auth=self._credentials)
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 404
        return response.status_code

    def get_num_of_patients(self) -> int:
        """
        Get number of patients available in the Blaze store
        :return: number of patients
        """
        try:
            return requests.get(url=self._blaze_url + "/Patient?_summary=count",
                                auth=self._credentials).json().get("total")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 0

    def is_patient_present_in_blaze(self, identifier: str) -> bool:
        """
        Checks if a patient is present in a blaze store
        :param identifier: of the Patient
        :return: true if present
        """
        try:
            response = (requests.get(url=self._blaze_url + "/Patient?identifier=" + identifier + "&_summary=count",
                                     auth=self._credentials)
                        .json()
                        .get("total"))
            return response > 0
        except TypeError:
            return False

    def sync_patients(self):
        """
        Syncs SampleDonors present in the repository and uploads them to the blaze store
        :return:
        """
        for donor in self._patient_service.get_all():
            if not self.is_patient_present_in_blaze(donor.identifier):
                try:
                    self.__upload_donor(donor)
                except requests.exceptions.ConnectionError:
                    logger.error("Cannot connect to blaze!")
                    return

    def __upload_donor(self, donor: SampleDonor) -> int:
        res = requests.post(url=self._blaze_url + "/Patient",
                            json=donor.to_fhir().as_json(),
                            auth=self._credentials)
        logger.info("Patient " + donor.identifier + " uploaded.")
        return res.status_code

    def delete_patient(self, identifier: str) -> int:
        """
        Deletes a Patient in the Blaze store
        :param identifier: of the Patient
        :return: Status code of the http request
        """
        list_of_full_urls = glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + identifier,
                                              auth=self._credentials)
                                 .json(), "**.fullUrl")
        for url in list_of_full_urls:
            logger.info("Deleting" + url)
            return requests.delete(url=url).status_code

    def sync_conditions(self):
        """Syncs Conditions present in the Condition Repository"""
        condition: Condition
        for condition in self._condition_service.get_all():
            patient_fhir_id = glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + condition.patient_id,
                                                auth=self._credentials)
                                   .json(), "**.resource.id")[0]
            res = requests.post(url=self._blaze_url + "/Condition",
                                json=condition.to_fhir(subject_id=patient_fhir_id).as_json(), auth=self._credentials)
            logger.info("Condition " + condition.icd_10_code + " for patient: " + patient_fhir_id + " uploaded.")
            return res.status_code

    def does_patient_have_condition(self, patient_identifier: str, icd_10_code: str) -> bool:
        """Checks if patient already has a condition with specific ICD-10 code (use dot format)"""
        patient_fhir_id = glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_identifier)
                               .json(), "**.resource.id")[0]
        search_url = f"{self._blaze_url}/Condition?patient={patient_fhir_id}" \
                     f"&code=http://hl7.org/fhir/sid/icd-10|{icd_10_code}"
        return requests.get(search_url).json().get("total") > 0
