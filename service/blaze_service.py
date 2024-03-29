import logging
import time

import requests
import schedule
from fhirclient.models.bundle import Bundle
from glom import glom

from exception.patient_not_found import PatientNotFoundError
from model.sample import Sample
from model.sample_donor import SampleDonor
from persistence.sample_collection_repository import SampleCollectionRepository
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import MATERIAL_TYPE_MAP, BLAZE_AUTH
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class BlazeService:
    """Service class for business operations/interactions with a Blaze FHIR server."""

    def __init__(self,
                 patient_service: PatientService, condition_service: ConditionService,
                 sample_service: SampleService,
                 blaze_url: str,
                 sample_collection_repository: SampleCollectionRepository
                 ):
        """
        Class for interacting with a Blaze Store FHIR server
        :param blaze_url: Base url of the FHIR server
        Must be without a trailing /.
        """
        self._patient_service = patient_service
        self._condition_service = condition_service
        self._sample_service = sample_service
        self._blaze_url = blaze_url
        self._sample_collection_repository = sample_collection_repository
        self._credentials = BLAZE_AUTH

    def sync(self):
        """Starts the sync between the repositories and the Blaze store."""
        logger.info("Starting sync with Blaze 🔥!")
        if self.get_number_of_resources("Patient") == 0:
            self.upload_sample_collections()
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
                    self.get_number_of_resources("Patient"))
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
                                     auth=self._credentials,
                                     verify=False)
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 404
        return response.status_code

    def sync_patients(self):
        """
        Syncs SampleDonors present in the repository and uploads them to the blaze store
        :return:
        """
        for donor in self._patient_service.get_all():
            if not self.is_resource_present_in_blaze(resource_type="patient",
                                                     identifier=donor.identifier):
                try:
                    self.__upload_donor(donor)
                except requests.exceptions.ConnectionError:
                    logger.error("Cannot connect to blaze!")
                    return

    def __upload_donor(self, donor: SampleDonor) -> int:
        logger.debug("Uploading patient: " + donor.to_fhir().as_json().__str__())
        res = requests.post(url=self._blaze_url + "/Patient",
                            json=donor.to_fhir().as_json(),
                            auth=self._credentials,
                            verify=False)
        logger.info("Patient " + donor.identifier + " uploaded.")
        return res.status_code

    def sync_conditions(self):
        """
        Syncs Conditions present in the Condition Repository
        """
        logger.info("Starting upload of conditions...")
        num_of_conditions_before_upload = self.get_number_of_resources("condition")
        logger.debug(f"Current number of conditions: {num_of_conditions_before_upload}")
        for condition in self._condition_service.get_all():
            try:
                patient_has_condition = self.patient_has_condition(patient_identifier=condition.patient_id,
                                                                   icd_10_code=condition.icd_10_code)
            except PatientNotFoundError:
                logger.info(f"Patient with identifier: {condition.patient_id} not present in the FHIR store."
                            f" Skipping...")
                continue
            if not patient_has_condition:
                self.__upload_condition(condition)
        logger.debug(
            f"Successfully uploaded {self.get_number_of_resources('Condition') - num_of_conditions_before_upload}"
            f" new conditions.")

    def __upload_condition(self, condition):
        patient_fhir_id = self.__get_fhir_id_of_donor(condition.patient_id)
        requests.post(url=self._blaze_url + "/Condition",
                      json=condition.to_fhir(subject_id=patient_fhir_id).as_json(),
                      auth=self._credentials,
                      verify=False)
        logger.debug(f"Condition {condition.icd_10_code} successfully uploaded for patient"
                     f"with FHIR id: {patient_fhir_id} and org. id: {condition.patient_id}.")

    def __get_fhir_id_of_donor(self, patient_id: str) -> str:
        """
        Get Resource id for a patient with identifier.
        :param patient_id: Identifier of the sample donor
        :return: FHIR resource id
        """
        return glom(requests.get(url=self._blaze_url + "/Patient?identifier=" + patient_id,
                                 auth=self._credentials, verify=False).json(), "**.resource.id")[0]

    def patient_has_condition(self, patient_identifier: str, icd_10_code: str) -> bool:
        """Checks if patient already has a condition with specific ICD-10 code (use a dot format)."""
        try:
            patient_fhir_id = glom(requests.get(url=f"{self._blaze_url}/Patient?identifier={patient_identifier}",
                                                auth=self._credentials,
                                                verify=False).json(), "**.resource.id")[0]
        except IndexError:
            raise PatientNotFoundError
        search_url = f"{self._blaze_url}/Condition?patient={patient_fhir_id}" \
                     f"&code=http://hl7.org/fhir/sid/icd-10|{icd_10_code}"
        return requests.get(search_url, auth=self._credentials, verify=False).json().get("total") > 0

    def sync_samples(self):
        """Syncs Samples present in the repository with the Blaze store."""
        logger.info("Starting upload of samples...")
        num_of_samples_before_sync = self.get_number_of_resources("Specimen")
        logger.debug(f"Current number of Specimens: {num_of_samples_before_sync}.")
        for sample in self._sample_service.get_all():
            logger.debug(f"Checking if Specimen with ID: {sample.identifier} is present."
                         f"Checking if Patient with ID: {sample.donor_id} is present")
            if (not self.is_resource_present_in_blaze(resource_type="Specimen", identifier=sample.identifier) and
                    self.is_resource_present_in_blaze(resource_type="Patient", identifier=sample.donor_id)):
                logger.debug(f"Specimen with org. ID: {sample.identifier} is not present in Blaze but the Donor is "
                             f"present. Uploading...")
                self.__upload_sample(sample)
                logger.debug(f"Successfully uploaded"
                             f" {self.get_number_of_resources('Specimen') - num_of_samples_before_sync}"
                             f"new samples.")

    def __upload_sample(self, sample: Sample):
        custodian_fhir_id: str = None
        if (sample.sample_collection_id is not None and
                self.is_resource_present_in_blaze("Organization", sample.sample_collection_id)):
            custodian_fhir_id = self.__get_organization_fhir_id(sample.sample_collection_id)
        requests.post(url=self._blaze_url + "/Specimen",
                      json=sample.to_fhir(material_type_map=MATERIAL_TYPE_MAP,
                                          subject_id=self.__get_fhir_id_of_donor(sample.donor_id),
                                          custodian_id=custodian_fhir_id)
                      .as_json(),
                      auth=self._credentials,
                      verify=False
                      )

    def __get_organization_fhir_id(self, organization_identifier: str):
        organization_fhir_id = \
            glom(requests.get(
                url=self._blaze_url + f"/Organization?identifier={organization_identifier}",
                auth=self._credentials, verify=False)
                 .json(), "**.resource.id")[0]
        return organization_fhir_id

    def get_number_of_resources(self, resource_type: str) -> int:
        """
        Get the number of Resources, of a specific type in the blaze store.
        :param resource_type: Resource type for which to get the count.
        :return: The number of resources in the Blaze store.
        """
        try:
            return requests.get(url=self._blaze_url + f"/{resource_type.capitalize()}?_summary=count",
                                auth=self._credentials, verify=False).json().get("total")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to blaze!")
            return 0

    def delete_fhir_resource(self, resource_type: str, param_value: str, search_param: str = "identifier") -> int:
        """
        Deletes all FHIR resources from the Blaze server of a specific type having a specific identifier.
        :param search_param: Parameter by which the resources are filtered. Default value is identifier
        :param param_value: actual value of the search parameter.
        (When using identifier, Identifier belonging to the resource. It is not the FHIR resource ID!)
        :param resource_type: Type of FHIR resource to delete.
        :return: Status code of the http request.
        """
        response = requests.get(url=self._blaze_url + f"/{resource_type.capitalize()}"
                                                      f"?{search_param}={param_value}",
                                auth=self._credentials,
                                verify=False)
        list_of_full_urls: list[str] = glom(response.json(), "**.fullUrl")
        if response.status_code == 404 or len(list_of_full_urls) == 0:
            return 404
        for url in list_of_full_urls:
            logger.info("Deleting " + url)
            if resource_type.capitalize() == "Patient":
                patient_reference = url[url.find("Patient/"):]
                logger.info(f"In order to delete Patient successfully, "
                            f"all resources which reference this patient needs to be deleted as well.")
                self.delete_fhir_resource("Condition", patient_reference, "reference")
                self.delete_fhir_resource("Specimen", patient_reference, "reference")
            deleted_resource = requests.get(url=url, auth=self._credentials).json()
            logger.debug(f"{deleted_resource}")
            delete_response = requests.delete(url=url, auth=self._credentials)
            if delete_response.status_code != 204:
                reason_index = delete_response.text.find("diagnostics")
                if reason_index != -1:
                    logger.debug(f"could not delete. Reason: {delete_response.text[reason_index:]}")
            logger.debug(f"response status: {delete_response.status_code}")
            return delete_response.status_code

    def is_resource_present_in_blaze(self, resource_type: str, identifier: str) -> bool:
        """
        Checks if a resource of specific type with a specific identifier is present in the Blaze store.
        :param resource_type: FHIR resource type.
        :param identifier: Identifier belonging to the resource.
        It is not the FHIR resource ID!
        :return:
        """
        try:
            count = (requests.get(
                url=self._blaze_url + f"/{resource_type.capitalize()}?identifier={identifier}&_summary=count",
                auth=self._credentials, verify=False)
                     .json()
                     .get("total"))
            logger.debug(f"Count of resource : {count} of type: {resource_type} with identifier :{identifier} ")
            return count > 0
        except TypeError:
            return False

    def upload_sample_collections(self):
        """Uploads SampleCollections as FHIR organizations."""
        for sample_collection in self._sample_collection_repository.get_all():
            if not self.is_resource_present_in_blaze(resource_type="Organization",
                                                     identifier=sample_collection.identifier):
                requests.post(url=self._blaze_url + "/Organization",
                              json=sample_collection.to_fhir().as_json(),
                              auth=self._credentials,
                              verify=False)
        logger.debug(f"Successfully uploaded {self.get_number_of_resources('Organization')} Sample collections.")
