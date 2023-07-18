import logging
import os

import requests
from fhirclient.models.bundle import Bundle
from glom import glom

from exception.patient_not_found import PatientNotFoundError
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
        :return: status code of the http request
        """
        bundle = self._patient_service.get_all_patients_in_fhir_transaction()
        return self.__post_bundle(bundle=bundle)

    def __post_bundle(self, bundle: Bundle) -> int:
        """
        Posts a bundle FHIR resource to Blaze store
        :param bundle: FHIR resource
        :return: http request status code
        """
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
        """
        Uploads a SampleDonor to the Blaze store
        :param donor: SampleDonor to upload
        :return: Status code of the http request
        """
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
            logger.info("Deleting " + url)
            return requests.delete(url=url).status_code

    def sync_conditions(self) -> int:
        """
        Syncs Conditions present in the Condition Repository
        :return: Number of conditions uploaded
        """
        counter = 0
        condition: Condition
        for condition in self._condition_service.get_all():
            try:
                patient_has_condition = self.patient_has_condition(patient_identifier=condition.patient_id,
                                                                   icd_10_code=condition.icd_10_code)
            except PatientNotFoundError:
                logger.info("Patient with identifier: " + condition.patient_id
                            + " not present in the FHIR store. Skipping...")
                continue
            if not patient_has_condition:
                self.__upload_condition(condition)
                counter += 1
        return counter

    def __upload_condition(self, condition):
        patient_fhir_id = self.__get_fhir_id_of_donor(condition.patient_id)
        requests.post(url=self._blaze_url + "/Condition",
                      json=condition.to_fhir(subject_id=patient_fhir_id).as_json(),
                      auth=self._credentials)
        logger.info("Condition " + condition.icd_10_code
                    + " for patient: " + patient_fhir_id + " uploaded.")

    def __get_fhir_id_of_donor(self, patient_id: str) -> str:
        """
        Get Resource id for a patient with identifier.
        :param patient_id: identifier of the sample donor
        :return: FHIR resource id
        """
        return glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_id,
                                 auth=self._credentials)
                    .json(), "**.resource.id")[0]

    def patient_has_condition(self, patient_identifier: str, icd_10_code: str) -> bool:
        """Checks if patient already has a condition with specific ICD-10 code (use dot format)"""
        try:
            patient_fhir_id = glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_identifier)
                                   .json(), "**.resource.id")[0]
        except IndexError:
            raise PatientNotFoundError
        search_url = f"{self._blaze_url}/Condition?patient={patient_fhir_id}" \
                     f"&code=http://hl7.org/fhir/sid/icd-10|{icd_10_code}"
        return requests.get(search_url, auth=self._credentials).json().get("total") > 0
