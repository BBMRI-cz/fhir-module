import logging
import os
import time

import requests
import schedule
from fhirclient.models.bundle import Bundle
from glom import glom

from exception.patient_not_found import PatientNotFoundError
from model.condition import Condition
from model.sample import Sample
from model.sample_donor import SampleDonor
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import MATERIAL_TYPE_MAP
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class BlazeService:
    def __init__(self, patient_service: PatientService, condition_service: ConditionService,
                 sample_service: SampleService, blaze_url: str):
        """
        Class for interacting with a Blaze Store FHIR server
        :param patient_service:
        :param blaze_url: Base url of the FHIR server.
        Must be without a trailing /
        """
        self._patient_service = patient_service
        self._condition_service = condition_service
        self._sample_service = sample_service
        self._blaze_url = blaze_url
        self._credentials = (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))

    def sync(self):
        """Starts the sync between the repositories and the Blaze store"""
        logger.info("Starting sync with Blaze 🔥!")
        if self.get_num_of_patients() == 0:
            self.initial_upload_of_all_patients()
            self.sync_conditions()
            self.sync_samples()
        else:
            logger.debug("Patients already present in the FHIR store.")
        self.__initialize_scheduler()
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __initialize_scheduler(self):
        logger.info("Initializing scheduler...")
        schedule.every().week.do(self.sync_patients)
        schedule.every().week.do(self.sync_conditions)
        schedule.every().week.do(self.sync_samples)
        logger.info("Scheduler initialized.")

    def initial_upload_of_all_patients(self) -> int:
        """
        This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
        patients. This method should be called only once, specifically if there are no patients in the FHIR server.
        :return: Status code of the http request
        """
        logger.info("Starting upload of patients...")
        bundle = self._patient_service.get_all_patients_in_fhir_transaction()
        status_code = self.__post_bundle(bundle=bundle)
        logger.info('Number of patients successfully uploaded: %s',
                    self.get_num_of_patients())
        return status_code

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
        Get the number of patients available in the Blaze store
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
        Checks if a patient with a specific organizational ID is present in a blaze store.
        :param identifier: Of the Patient
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
        logger.debug("Uploading patient: " + donor.to_fhir().as_json().__str__())
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
            deleted_patient = requests.get(url=url, auth=self._credentials).json()
            logger.debug(f"{deleted_patient}")
            logger.info("Deleting " + url)
            return requests.delete(url=url).status_code

    def sync_conditions(self):
        """
        Syncs Conditions present in the Condition Repository
        """
        logger.info("Starting upload of conditions...")
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

    def __upload_condition(self, condition):
        patient_fhir_id = self.__get_fhir_id_of_donor(condition.patient_id)
        requests.post(url=self._blaze_url + "/Condition",
                      json=condition.to_fhir(subject_id=patient_fhir_id).as_json(),
                      auth=self._credentials)
        logger.debug(f"Condition {condition.icd_10_code} successfully uploaded for patient"
                     f"with FHIR id: {patient_fhir_id} and org. id: {condition.patient_id}.")

    def __get_fhir_id_of_donor(self, patient_id: str) -> str:
        """
        Get Resource id for a patient with identifier.
        :param patient_id: Identifier of the sample donor
        :return: FHIR resource id
        """
        return glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_id,
                                 auth=self._credentials)
                    .json(), "**.resource.id")[0]

    def patient_has_condition(self, patient_identifier: str, icd_10_code: str) -> bool:
        """Checks if patient already has a condition with specific ICD-10 code (use a dot format)"""
        try:
            patient_fhir_id = glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_identifier)
                                   .json(), "**.resource.id")[0]
        except IndexError:
            raise PatientNotFoundError
        search_url = f"{self._blaze_url}/Condition?patient={patient_fhir_id}" \
                     f"&code=http://hl7.org/fhir/sid/icd-10|{icd_10_code}"
        return requests.get(search_url, auth=self._credentials).json().get("total") > 0

    def sync_samples(self):
        """Syncs Samples present in the repository with the Blaze store."""
        logger.info("Starting upload of samples...")
        sample: Sample
        for sample in self._sample_service.get_all():
            if not self.is_specimen_present_in_blaze(sample.identifier) and self.is_patient_present_in_blaze(
                    sample.donor_id):
                logger.debug(f"Specimen with org. ID: {sample.identifier} is not present in Blaze but the Donor is "
                             f"present. Uploading...")
                patient_fhir_id = glom(requests.get(url=self._blaze_url + f"/Patient?identifier={sample.donor_id}")
                                       .json(), "**.resource.id")[0]
                requests.post(url=self._blaze_url + "/Specimen",
                              json=sample.to_fhir(material_type_map=MATERIAL_TYPE_MAP, subject_id=patient_fhir_id)
                              .as_json(),
                              auth=self._credentials)

    def get_num_of_specimens(self) -> int:
        """
        Get the number of specimens available in the Blaze store
        :return: number of specimens
        """
        try:
            return requests.get(url=self._blaze_url + "/Specimen?_summary=count",
                                auth=self._credentials).json().get("total")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 0

    def delete_specimen(self, identifier: str) -> int:
        """
        Deletes a Specimen in the Blaze store
        :param identifier: of the Specimen
        :return: Status code of the http request
        """
        list_of_full_urls = glom(requests.get(url=self._blaze_url + "/Specimen?identifier=" + identifier,
                                              auth=self._credentials)
                                 .json(), "**.fullUrl")
        for url in list_of_full_urls:
            deleted_specimen = requests.get(url=url, auth=self._credentials).json()
            logger.debug(f"{deleted_specimen}")
            logger.info("Deleting " + url)
            return requests.delete(url=url).status_code

    def is_specimen_present_in_blaze(self, identifier: str) -> bool:
        """
        Checks if a specimen is present in a blaze store
        :param identifier: of the Specimen
        :return: true if present
        """
        try:
            response = (requests.get(url=self._blaze_url + "/Specimen?identifier=" + identifier + "&_summary=count",
                                     auth=self._credentials)
                        .json()
                        .get("total"))
            return response > 0
        except TypeError:
            return False
