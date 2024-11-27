import time
from typing import cast

import requests
import schedule
from blaze_client import BlazeClient, NonExistentResourceException
import logging

from miabis_model.util.parsing_util import get_nested_value

from model.miabis.collection_miabis import CollectionMiabis
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.miabis.sample_miabis import SampleMiabis
from persistence.biobank_repository import BiobankRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from service.blaze_service_interface import BlazeServiceInterface

from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import MIABIS_BLAZE_AUTH
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class MiabisBlazeService(BlazeServiceInterface):
    def __init__(self,
                 patient_service: PatientService,
                 sample_service: SampleService,
                 blaze_url: str,
                 sample_collection_repository: SampleCollectionRepository,
                 biobank_repository: BiobankRepository
                 ):
        self.blaze_client = BlazeClient(blaze_url=blaze_url, blaze_username=MIABIS_BLAZE_AUTH[0], blaze_password=MIABIS_BLAZE_AUTH[1])
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
        try:
            if not self.blaze_client.is_resource_present_in_blaze("Organization", biobank.identifier, "identifier"):
                logger.info(
                    f"MIABIS on FHIR: Biobank with identifier {biobank.identifier} not present in blaze. uploading...")

                self.blaze_client.upload_biobank(biobank)

                logger.info(f"MIABIS on FHIR: Successfully uploaded biobank.")
            else:
                logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank} is already present in blaze.")
            logger.info(f"MIABIS on FHIR: Starting upload of collections")
            for collection in self.sample_collection_repository.get_all():
                if not isinstance(collection, CollectionMiabis):
                    logger.error(
                        f"MIABIS ON FHIR: collection is not instance of MIABIS on FHIR model, but rather its type is {type(collection)} Skipping...")
                    continue
                collection = cast(CollectionMiabis, collection)
                if not self.blaze_client.is_resource_present_in_blaze("Organization", collection.identifier,
                                                                      "identifier"):
                    logger.debug(
                        f"MIABIS on FHIR: Collection with identifier {collection.identifier} is not present. Uploading...")
                    self.blaze_client.upload_collection(collection)
                    logger.debug(
                        f"MIABIS on FHIR: Sucessfully uploaded collection with identifier {collection.identifier}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to the blaze server!")
            return
        except (ValueError, KeyError, TypeError) as err:
            logger.error(f"{err}")
            return
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
            if not self.blaze_client.is_resource_present_in_blaze("Patient", donor.identifier, "identifier"):
                self.blaze_client.upload_donor(donor)
                logger.debug(f"MIABIS ON FHIR: successfully uploaded patient with identifier {donor.identifier}")
            else:
                logger.debug(f"MIABIS on FHIR: donor with id {donor.identifier} already present. Checking if all the data about the patient are same")
                donor_fhir_id = self.blaze_client.get_fhir_id("Patient",donor.identifier)
                donor_from_blaze = self.blaze_client.build_donor_from_json(donor_fhir_id)
                if donor != donor_from_blaze:
                    logger.debug(f"MIABIS on FHIR: donor resource is different from donor that is already in blaze. Updating....")
                    self.blaze_client.update_donor(donor)
        logger.info(f"MIABIS on FHIR: Upload of donor resources is done.")

    def upload_samples(self):
        logger.info("MIABIS on FHIR: Starting upload of samples...")
        collection_with_new_samples_map = {}
        for sample in self.sample_service.get_all():
            if not isinstance(sample, SampleMiabis):
                logger.error(f"MIABIS on FHIR: sample is not instance of MIABIS on FHIR model, "
                             f"but rather its type is {type(sample)}. Skipping....")
                continue
            sample = cast(SampleMiabis, sample)
            try:
                if not self.blaze_client.is_resource_present_in_blaze("Specimen", sample.identifier, "identifier"):

                        sample_fhir_id = self.blaze_client.upload_sample(sample)

                        logger.debug(f"MIABIS on FHIR: Successfully uploaded sample with id {sample.identifier}")
                        patient_fhir_id = self.blaze_client.get_fhir_id("Patient", sample.donor_identifier)
                        if not self.blaze_client.is_resource_present_in_blaze("Condition", patient_fhir_id,
                                                                              "subject"):
                            logger.debug(
                                f"MIABIS on FHIR: Condition for patient : {sample.donor_identifier} is not present. Uploading new condition")

                            self.blaze_client.upload_condition(sample.condition)
                            logger.debug(f"MIABIS on FHIR: Succesfully uploaded new Condition")
                        else:
                            condition_fhir_id = self.blaze_client.get_condition_by_patient_fhir_id(patient_fhir_id)
                            self.blaze_client.add_diagnoses_to_condition(condition_fhir_id, sample_fhir_id)
                        if sample.sample_collection_id is not None:
                            collection_with_new_samples_map.setdefault(sample.sample_collection_id, []).append(
                                sample_fhir_id)
                else:
                    logger.debug(f"MIABIS on FHIR: sample with id {sample.identifier}  is already present in the blaze store. Checking if the data of sample are same.")
                    sample_fhir_id = self.blaze_client.get_fhir_id("Specimen",sample.identifier)
                    sample_from_blaze = self.blaze_client.build_sample_from_json(sample_fhir_id)
                    if sample != sample_from_blaze:
                        logger.debug(f"MIABIS on FHIR: sample is different than the sample already present in the blaze. Updating.")
                        sample_fhir_id = self.blaze_client.update_sample(sample)
                        patient_fhir_id = self.blaze_client.get_fhir_id("Patient", sample.donor_identifier)
                        condition_fhir_id = self.blaze_client.get_condition_by_patient_fhir_id(patient_fhir_id)
                        self.blaze_client.add_diagnoses_to_condition(condition_fhir_id, sample_fhir_id)
                        if sample.sample_collection_id is not None:
                            collection_with_new_samples_map.setdefault(sample.sample_collection_id, []).append(
                                sample_fhir_id)
            except NonExistentResourceException as err:
                logger.error(f"MIABIS on FHIR: {err}")

        for collection_id, sample_fhir_ids in collection_with_new_samples_map.items():
            logger.info(f"MIABIS on FHIR: adding samples to the respective collection with identifier {collection_id}")
            collection_fhir_id = self.blaze_client.get_fhir_id("Group", collection_id)
            updated = self.blaze_client.add_already_present_samples_to_existing_collection(sample_fhir_ids,
                                                                                           collection_fhir_id)
            if updated:
                logger.info(f"MIABIS on FHIR: Successfully updated Collection {collection_id} with new values")
            else:
                logger.info(f"MIABIS on FHIR: Collection {collection_id}  was not updated.")
        logger.info(f"MIABIS on FHIR: upload of samples is done.")

    def delete_everything(self):
        """Just as name says.DELETES EVERYTHING!!!"""
        biobank = self.biobank_repository.get_biobank()
        logger.info("MIABIS on FHIR:Deleting all resouces from Blaze. It may take a while...")
        self.blaze_client.delete_all_resources(biobank.identifier)
        logger.info("MIABIS on FHIR: Resources deleted.")
        return True

    def __initialize_scheduler(self):
        logger.info("Initializing scheduler....")
        schedule.every().week.do(self.sync_biobank_and_collections())
        schedule.every().week.do(self.upload_samples())
        schedule.every().week.do(self.upload_patients())
        logger.info("Scheduler initialized.")

    def run_scheduler(self):
        self.__initialize_scheduler()
        logger.info("Running Scheduler.")
        while True:
            schedule.run_pending()
            time.sleep(1)