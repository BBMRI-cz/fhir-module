from typing import cast

from blaze_client import BlazeClient, NonExistentResourceException
import logging

from miabis_model.util.parsing_util import get_nested_value

from model.miabis.collection_miabis import CollectionMiabis
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.miabis.sample_miabis import SampleMiabis
from persistence.biobank_repository import BiobankRepository
from persistence.sample_collection_repository import SampleCollectionRepository

from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import BLAZE_AUTH
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class MiabisBlazeService(BlazeClient):
    def __init__(self,
                 patient_service: PatientService,
                 sample_service: SampleService,
                 blaze_url: str,
                 sample_collection_repository: SampleCollectionRepository,
                 biobank_repository: BiobankRepository
                 ):
        super().__init__(blaze_url=blaze_url, blaze_username=BLAZE_AUTH[0], blaze_password=BLAZE_AUTH[1])
        self.patient_service = patient_service
        self.sample_service = sample_service
        self.sample_collection_repository = sample_collection_repository
        self.biobank_repository = biobank_repository

    def sync(self):

        self.sync_biobank_and_collections()
        self.upload_patients()
        self.upload_samples()

    def sync_biobank_and_collections(self):
        biobank = self.biobank_repository.get_biobank()
        if not self.is_resource_present_in_blaze("Organization",biobank.identifier,"identifier"):
            logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank.identifier} not present in blaze. uploading...")
            biobank_fhir_id = self.upload_biobank(biobank)
            logger.info(f"MIABIS on FHIR: Successfully uploaded biobank.")
        else:
            logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank} is already present in blaze.")
        for collection in self.sample_collection_repository.get_all():
            if not isinstance(collection,CollectionMiabis):
                logger.error(f"MIABIS ON FHIR: collection is not instance of MIABIS on FHIR model, but rather its type is {type(collection)} Skipping...")
                continue
            collection = cast(CollectionMiabis, collection)
            if not self.is_resource_present_in_blaze("Organization",collection.identifier,"identifier"):
                # TODO maybe check collection organization,a nd collection aswell ?
                logger.info(f"MIABIS on FHIR: Collection with identifier {collection.identifier} is not present. Uploading...")
                collection_organization_fhir_id = self.upload_collection_organization(collection)
                collection_fhir_id = self.upload_collection(collection.collection)
                logger.info(f"MIABIS on FHIR: Sucessfully uploaded collection with identifier {collection.identifier}")
        logger.info(f"MIABIS on FHIR: Sync of biobank and collection resources is done.")



    def upload_patients(self):
        """
        This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
        patients. This method should be called only once, specifically if there are no patients in the FHIR server.
                """
        logger.info(f"MIABIS on FHIR: Starting upload of donors")
        for donor in self.patient_service.get_all():
            if not isinstance(donor, SampleDonorMiabis):
                logger.error(
                    f"donor is not instance of MIABIS on FHIR model, but rather its type is {type(donor)}. Skipping....")
                continue
            donor = cast(SampleDonorMiabis, donor)
            if not self.is_resource_present_in_blaze("Patient", donor.identifier, "identifier"):
                patient_fhir_id = self.upload_donor(donor)

                logger.info(f"MIABIS ON FHIR: successfully uploaded patient with identifier {donor.identifier}")
        logger.info(f"MIABIS on FHIR: Upload of donor resources is done.")

    def upload_samples(self):
        logger.info("MIABIS on FHIR: Starting upload of samples...")
        collection_with_new_samples_map = {}
        #  TODO num_of_samples_before_sync
        for sample in self.sample_service.get_all():
            if not isinstance(sample, SampleMiabis):
                logger.error(f"MIABIS on FHIR: sample is not instance of MIABIS on FHIR model, "
                             f"but rather its type is {type(sample)}. Skipping....")
            sample = cast(SampleMiabis, sample)
            if not self.is_resource_present_in_blaze("Specimen", sample.identifier, "identifier"):
                try:
                    sample_fhir_id = self.upload_sample(sample)
                    logger.info(f"MIABIS on FHIR: Successfully uploaded sample with id {sample.identifier}")
                    for observation in sample.observations:
                        logger.info(
                            f"MIABIS on FHIR: Successfully uploaded observation with diagnosis {observation.icd10_code}")
                        self.upload_observation(observation)
                    diagnosis_report_fhir_id = self.upload_diagnosis_report(sample.diagnosis_report)
                    logger.info(
                        f"MIABIS on FHIR: Successfully uploaded diagnosis report for sample : {sample.identifier} and patient {sample.donor_identifier}")
                    if not self.is_resource_present_in_blaze("Condition", sample.donor_identifier, "subject"):
                        logger.info(
                            f"MIABIS on FHIR: Condition for patient : {sample.donor_identifier} is not present. Uploading new condition")
                        self.upload_condition(sample.condition)
                        logger.info(f"MIABIS on FHIR: Succesfully uploaded new Condition")
                    else:
                        # TODO need to be able to find condition
                        patient_fhir_id = self.get_fhir_id("Patient", sample.donor_identifier)
                        condition_fhir_id = self.get_condition_by_patient_fhir_id(patient_fhir_id)
                        self.add_diagnosis_reports_to_condition(condition_fhir_id, [diagnosis_report_fhir_id])
                    if sample.sample_collection_id is not None:
                        collection_with_new_samples_map.setdefault(sample.sample_collection_id,[]).append(sample_fhir_id)
                except NonExistentResourceException as err:
                    logger.error(f"MIABIS on FHIR: {err}")
        for collection_id,sample_fhir_ids in collection_with_new_samples_map.items():
            logger.info(f"MIABIS on FHIR: adding samples to the respective collection with identifier {collection_id}")
            collection_fhir_id = self.get_fhir_id("Group",collection_id)
            updated = self.add_already_present_samples_to_existing_collection(sample_fhir_ids,collection_fhir_id)
            if updated:
                logger.info(f"MIABIS on FHIR: Successfully updated Collection {collection_id} with new values")
            else:
                logger.info(f"MIABIS on FHIR: Collection {collection_id}  was not updated.")
        logger.info(f"MIABIS on FHIR: upload of samples is done.")


