import logging
import time

import requests
import schedule
from requests.adapters import HTTPAdapter, Retry
from fhirclient.models.bundle import Bundle
from glom import glom, Iter, T, Coalesce

from exception.patient_not_found import PatientNotFoundError
from model.sample import Sample
from model.sample_donor import SampleDonor
from persistence.sample_collection_repository import SampleCollectionRepository
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import MATERIAL_TYPE_MAP, BLAZE_AUTH
from util.custom_logger import setup_logger
from util.sample_util import build_sample_from_json

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
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])
        session = requests.session()
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.auth = BLAZE_AUTH
        self._session = session

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
        schedule.every().week.do(self.upload_sample_collections)
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
            response = self._session.post(url=self._blaze_url,
                                          json=bundle.as_json(),
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
        res = self._session.post(url=self._blaze_url + "/Patient",
                                 json=donor.to_fhir().as_json(),
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
        self._session.post(url=self._blaze_url + "/Condition",
                           json=condition.to_fhir(subject_id=patient_fhir_id).as_json(),
                           verify=False)
        logger.debug(f"Condition {condition.icd_10_code} successfully uploaded for patient"
                     f"with FHIR id: {patient_fhir_id} and org. id: {condition.patient_id}.")

    def __get_fhir_id_of_donor(self, patient_id: str) -> str:
        """
        Get Resource id for a patient with identifier.
        :param patient_id: Identifier of the sample donor
        :return: FHIR resource id
        """
        return glom(self._session.get(url=self._blaze_url + "/Patient?identifier=" + patient_id,
                                      verify=False).json(), "**.resource.id")[0]

    def patient_has_condition(self, patient_identifier: str, icd_10_code: str) -> bool:
        """Checks if patient already has a condition with specific ICD-10 code (use a dot format)."""
        try:
            patient_fhir_id = glom(self._session.get(url=f"{self._blaze_url}/Patient?identifier={patient_identifier}",
                                                     verify=False).json(), "**.resource.id")[0]
        except IndexError:
            raise PatientNotFoundError
        search_url = f"{self._blaze_url}/Condition?patient={patient_fhir_id}" \
                     f"&code=http://hl7.org/fhir/sid/icd-10|{icd_10_code}"
        return self._session.get(search_url, verify=False).json().get("total") > 0

    def sync_samples(self):
        """Syncs Samples present in the repository with the Blaze store."""
        logger.info("Starting upload of samples...")
        num_of_samples_before_sync = self.get_number_of_resources("Specimen")
        logger.debug(f"Current number of Specimens: {num_of_samples_before_sync}.")
        for sample in self._sample_service.get_all():
            logger.debug(f"Checking if Specimen with ID: {sample.identifier} is present."
                         f"Checking if Patient with ID: {sample.donor_id} is present")

            specimen_present = self.is_resource_present_in_blaze(resource_type="Specimen", identifier=sample.identifier)
            patient_present = self.is_resource_present_in_blaze(resource_type="Patient", identifier=sample.donor_id)

            if not specimen_present and patient_present:
                logger.debug(f"Specimen with org. ID: {sample.identifier} is not present in Blaze but the Donor is "
                             f"present. Uploading...")
                self.__upload_sample(sample)
                logger.debug(f"Successfully uploaded"
                             f" {self.get_number_of_resources('Specimen') - num_of_samples_before_sync}"
                             f"new samples.")
            elif specimen_present and patient_present:
                logger.debug(f"Specimen with org. ID: {sample.identifier} is already present in Blaze."
                             f"Checking if the sample is up to date.")
                old_sample = self.__build_existing_sample(sample)
                if sample == old_sample:
                    continue
                else:
                    old_sample_id = self.__get_fhir_sample_id(sample.identifier)
                    sample.update_diagnoses(old_sample.diagnoses)
                    self.__update_sample(sample, old_sample_id)

    def __upload_sample(self, sample: Sample):
        custodian_fhir_id: str = None
        if (sample.sample_collection_id is not None and
                self.is_resource_present_in_blaze("Organization", sample.sample_collection_id)):
            custodian_fhir_id = self.__get_organization_fhir_id(sample.sample_collection_id)
        response = self._session.post(url=self._blaze_url + "/Specimen",
                                      json=sample.to_fhir(material_type_map=MATERIAL_TYPE_MAP,
                                                          subject_id=self.__get_fhir_id_of_donor(sample.donor_id),
                                                          custodian_id=custodian_fhir_id)
                                      .as_json(),
                                      verify=False
                                      )
        if response.status_code != 201:
            logger.error(f"Failed to upload sample with ID: {sample.identifier}. Reason: {response.text}")

    def __update_sample(self, updated_sample: Sample, sample_fhir_id: str):
        """
        Updates a sample in the Blaze store.
        :param sample: Sample object to update.
        :param sample_fhir_id: FHIR resource ID of the sample.
        """
        custodian_fhir_id: str = None
        if (updated_sample.sample_collection_id is not None and
                self.is_resource_present_in_blaze("Organization", updated_sample.sample_collection_id)):
            custodian_fhir_id = self.__get_organization_fhir_id(updated_sample.sample_collection_id)
        updated_sample_fhir = updated_sample.to_fhir(material_type_map=MATERIAL_TYPE_MAP,
                                                     subject_id=self.__get_fhir_id_of_donor(updated_sample.donor_id),
                                                     custodian_id=custodian_fhir_id).as_json()
        updated_sample_fhir["id"] = sample_fhir_id
        response = self._session.put(url=self._blaze_url + f"/Specimen/{sample_fhir_id}",
                                     json=updated_sample_fhir,
                                     verify=False
                                     )
        if response.status_code == 200:
            logger.info(f"Sample with ID: {updated_sample.identifier} successfully updated.")
        else:
            logger.error(f"Failed to update sample with ID: {updated_sample.identifier}. Reason: {response.text}")

    def __build_existing_sample(self, new_sample: Sample) -> Sample:
        """
        Builds a Sample object from the Blaze store using the identifier of the new Sample object.
        :param new_sample: sample to be added (the existing sample is to be built using this sample's FHIR ID)
        """
        fhir_sample_id = self.__get_fhir_sample_id(new_sample.identifier)
        fhir_sample = self._session.get(url=self._blaze_url + f"/Specimen/{fhir_sample_id}",
                                        verify=False).json()
        old_donor_id = glom(fhir_sample, ("**.subject", ["reference"]))[0]
        old_sample_donor_identifier = self.__get_donor_identifier(old_donor_id)
        old_sample_collection_identifier = None
        if fhir_sample.get("extension") is not None:
            for ext in fhir_sample.get("extension"):
                if ext.get("url") == "https://fhir.bbmri.de/StructureDefinition/Custodian":
                    old_sample_collection_id = ext.get("valueReference").get("reference")
                    old_sample_collection_identifier = self.__get_collection_identifier(old_sample_collection_id)
        old_sample = build_sample_from_json(fhir_sample, old_sample_donor_identifier, old_sample_collection_identifier)
        return old_sample

    def __get_organization_fhir_id(self, organization_identifier: str):
        organization_fhir_id = \
            glom(self._session.get(
                url=self._blaze_url + f"/Organization?identifier={organization_identifier}", verify=False)
                 .json(), "**.resource.id")[0]
        return organization_fhir_id

    def get_number_of_resources(self, resource_type: str) -> int:
        """
        Get the number of Resources, of a specific type in the blaze store.
        :param resource_type: Resource type for which to get the count.
        :return: The number of resources in the Blaze store.
        """
        try:
            return self._session.get(url=self._blaze_url + f"/{resource_type.capitalize()}?_summary=count",
                                     verify=False).json().get("total")
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
        response = self._session.get(url=self._blaze_url + f"/{resource_type.capitalize()}"
                                                           f"?{search_param}={param_value}",
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
            deleted_resource = self._session.get(url=url).json()
            logger.debug(f"{deleted_resource}")
            delete_response = self._session.delete(url=url)
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
            count = (self._session.get(
                url=self._blaze_url + f"/{resource_type.capitalize()}?identifier={identifier}&_summary=count",
                verify=False)
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
                self._session.post(url=self._blaze_url + "/Organization",
                                   json=sample_collection.to_fhir().as_json(),
                                   verify=False)
        logger.debug(f"Successfully uploaded {self.get_number_of_resources('Organization')} Sample collections.")

    def get_sample_collection_id(self, sample_identifier: str) -> str | None:
        """Get the identifier of the Sample Collection to which a sample belongs.
        :param sample_identifier: Identifier of the sample.
        :return: Identifier of the Sample Collection. if not found, returns None."""
        sample_id = self.__get_fhir_sample_id(sample_identifier)
        sample = self._session.get(url=self._blaze_url + f"/Specimen/{sample_id}", verify=False).json()
        sample_collection_id = None
        if sample.get("extension") is not None:
            for ext in sample.get("extension"):
                if ext.get("url") == "https://fhir.bbmri.de/StructureDefinition/Custodian":
                    sample_collection_id = ext.get("valueReference").get("reference")
        return sample_collection_id

    def get_diagnoses_from_sample(self, sample_identifier: str) -> list[str]:
        """Get diagnoses from a sample in the Blaze store.
        :param sample_identifier: Identifier of the sample.
        :return: List of diagnoses."""
        sample_id = self.__get_fhir_sample_id(sample_identifier)
        sample: dict = self._session.get(url=self._blaze_url + f"/Specimen/{sample_id}", verify=False).json()
        diagnoses = []
        if sample.get("extension") is not None:
            for ext in sample.get("extension"):
                if ext.get("url") == "https://fhir.bbmri.de/StructureDefinition/SampleDiagnosis":
                    diagnoses.append(ext.get("valueCodeableConcept").get("coding")[0].get("code"))

        return diagnoses

    def get_storage_temperature_from_sample(self, sample_identifier: str) -> str | None:
        """Get storage temperature from a sample in the Blaze store.
        :param sample_identifier: Identifier of the sample.
        :return: Storage temperature."""
        sample_id = self.__get_fhir_sample_id(sample_identifier)
        sample: dict = self._session.get(url=self._blaze_url + f"/Specimen/{sample_id}", verify=False).json()
        storage_temperature = None
        if sample.get("extension") is not None:
            for ext in sample.get("extension"):
                if ext.get("url") == "https://fhir.bbmri.de/StructureDefinition/StorageTemperature":
                    storage_temperature = ext.get("valueCodeableConcept").get("coding")[0].get("code")

        return storage_temperature

    def __get_fhir_sample_id(self, sample_identifier: str) -> str:
        """Get the FHIR resource ID of a sample using the sample identifier.
        :param sample_identifier: Identifier of the sample.
        :return: FHIR resource ID of the sample."""

        sample = self._session.get(url=self._blaze_url + f"/Specimen?identifier={sample_identifier}",
                                   verify=False).json()
        return glom(sample, "**.resource.id")[0]

    def __get_collection_identifier(self, fhir_collection_id: str) -> str | None:
        """Get the identifier of the Sample Collection to which a sample belongs.
        :param fhir_collection_id: FHIR resource ID of the Sample Collection.
        :return: Identifier of the Sample Collection. if not found, returns None."""
        collection = self._session.get(url=self._blaze_url + f"/{fhir_collection_id}").json()
        identifier_list = (glom(collection, ("**.identifier", ["**.value"]), default=None))
        if len(identifier_list) > 0:
            return self.__flatten_list(identifier_list)[0]
        return None

    def __get_donor_identifier(self, fhir_patient_id: str) -> str | None:
        """Get the identifier of the Sample Donor from the Blaze store.
        :param fhir_patient_id: FHIR resource ID of the Sample Donor.
        :return: Identifier of the Sample Donor. if not found, returns None."""
        patient = self._session.get(url=self._blaze_url + f"/{fhir_patient_id}").json()

        identifier_list = glom(patient, ("**.identifier", ["**.value"]), default=None)
        if len(identifier_list) > 0:
            return self.__flatten_list(identifier_list)[0]
        return None

    def __flatten_list(self, nested_list):
        """Flatten a nested list."""
        return [item for sublist in nested_list for item in
                (self.__flatten_list(sublist) if isinstance(sublist, list) else [sublist])]
