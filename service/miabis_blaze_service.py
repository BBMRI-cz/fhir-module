import time
from typing import cast

import requests
import schedule
from blaze_client import BlazeClient, NonExistentResourceException
import logging
import json

from requests import HTTPError

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
from util.metrics import get_metrics_for_service

setup_logger()
logger = logging.getLogger()
sync_logger = logging.getLogger("miabis_sync_logger")


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
        self.metrics = get_metrics_for_service('miabis_blaze')

    def sync(self):
        biobank_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
        collection_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
        pat_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
        samp_summary = {'processed': 0, 'failed': 0, 'skipped': 0}

        try:
            biobank_collection_summary = self.sync_biobank_and_collections()
            biobank_summary = biobank_collection_summary['biobank']
            collection_summary = biobank_collection_summary['collections']
            pat_summary = self.upload_patients()
            samp_summary = self.upload_samples()

            if self.metrics:
                self.metrics.set_metric('last_sync_timestamp', time.time())

            sync_summary_obj = {
                'patients': pat_summary,
                'specimens': samp_summary,
                'biobank': biobank_summary,
                'collections': collection_summary,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'success': True
            }
            sync_logger.info(json.dumps({'sync_summary': sync_summary_obj}))

            logger.info("MIABIS on FHIR: Sync completed successfully!")
        except Exception as e:
            logger.error(f"MIABIS on FHIR: Sync failed: {e}")
            
            sync_summary_obj = {
                'patients': pat_summary,
                'specimens': samp_summary,
                'biobank': biobank_summary,
                'collections': collection_summary,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'success': False,
                'error_message': str(e)
            }
            sync_logger.info(json.dumps({'sync_summary': sync_summary_obj}))

    def sync_biobank_and_collections(self):
        biobank_processed = 0
        biobank_failed = 0
        biobank_skipped = 0
        
        collection_processed = 0
        collection_failed = 0
        collection_skipped = 0
        
        biobank = self.biobank_repository.get_biobank()
        try:
            if not self.blaze_client.is_resource_present_in_blaze("Organization", biobank.identifier, "identifier"):
                logger.info(
                    f"MIABIS on FHIR: Biobank with identifier {biobank.identifier} not present in blaze. uploading...")

                self.blaze_client.upload_biobank(biobank)
                biobank_processed += 1

                logger.info(f"MIABIS on FHIR: Successfully uploaded biobank.")
            else:
                logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank} is already present in blaze.")
                biobank_skipped += 1
                
            logger.info(f"MIABIS on FHIR: Starting upload of collections")
            for collection in self.sample_collection_repository.get_all():
                if not isinstance(collection, CollectionMiabis):
                    logger.error(
                        f"MIABIS ON FHIR: collection is not instance of MIABIS on FHIR model, but rather its type is {type(collection)} Skipping...")
                    collection_skipped += 1
                    continue

                collection = cast(CollectionMiabis, collection)

                if self.blaze_client.is_resource_present_in_blaze("Organization", collection.identifier,
                                                                      "identifier"):
                    collection_skipped += 1
                    continue

                try:
                    logger.debug(
                        f"MIABIS on FHIR: Collection with identifier {collection.identifier} is not present. Uploading...")
                    self.blaze_client.upload_collection(collection)
                    collection_processed += 1
                    logger.debug(
                        f"MIABIS on FHIR: Sucessfully uploaded collection with identifier {collection.identifier}")
                except Exception as e:
                    logger.error(f"MIABIS on FHIR: Error uploading collection {collection.identifier}: {e}")
                    collection_failed += 1

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to the blaze server!")
            biobank_failed += 1
        except (ValueError, KeyError, TypeError, HTTPError) as err:
            logger.error(f"{err}")
            biobank_failed += 1
        else:
            logger.info(f"MIABIS on FHIR: Sync of biobank and collection resources is done.")

        return {
            'biobank': {'processed': biobank_processed, 'failed': biobank_failed, 'skipped': biobank_skipped},
            'collections': {'processed': collection_processed, 'failed': collection_failed, 'skipped': collection_skipped}
        }

    def __validate_donor_type(self, donor) -> SampleDonorMiabis | None:
        """Validate that donor is of correct type and return cast donor or None if invalid."""
        if not isinstance(donor, SampleDonorMiabis):
            logger.error(
                f"donor is not instance of MIABIS on FHIR model, but rather its type is {type(donor)}. Skipping....")
            return None
        return cast(SampleDonorMiabis, donor)

    def __process_new_donor_upload(self, donor: SampleDonorMiabis) -> tuple[int, int]:
        """Process upload of a new donor. Returns (processed_count, failed_count)."""
        try:
            self.blaze_client.upload_donor(donor)
            logger.debug(f"MIABIS ON FHIR: successfully uploaded patient with identifier {donor.identifier}")
            return 1, 0
        except HTTPError as e:
            logger.error(f"Error uploading the patient: {e}")
            return 0, 1

    def __process_existing_donor_update(self, donor: SampleDonorMiabis) -> tuple[int, int, int]:
        """Process update of an existing donor. Returns (processed_count, failed_count, skipped_count)."""
        logger.debug(f"MIABIS on FHIR: donor with id {donor.identifier} already present. Checking if all the data about the patient are same")
        
        donor_fhir_id = self.blaze_client.get_fhir_id("Patient", donor.identifier)
        donor_from_blaze = self.blaze_client.build_donor_from_json(donor_fhir_id)
        
        if donor != donor_from_blaze:
            logger.debug(f"MIABIS on FHIR: donor resource is different from donor that is already in blaze. Updating....")
            try:
                self.blaze_client.update_donor(donor)
                return 1, 0, 0
            except Exception as e:
                logger.error(f"MIABIS on FHIR: Error updating donor {donor.identifier}: {e}")
                return 0, 1, 0
        else:
            return 0, 0, 1

    def upload_patients(self):
        """
        This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
        patients. This method should be called only once, specifically if there are no patients in the FHIR server.
        """
        logger.info(f"MIABIS on FHIR: Starting upload of donors")
        processed = 0
        failed = 0
        skipped = 0
        
        for donor in self.patient_service.get_all():
            validated_donor = self.__validate_donor_type(donor)
            if validated_donor is None:
                skipped += 1
                continue
                
            if not self.blaze_client.is_resource_present_in_blaze("Patient", validated_donor.identifier, "identifier"):
                new_processed, new_failed = self.__process_new_donor_upload(validated_donor)
                processed += new_processed
                failed += new_failed
            else:
                new_processed, new_failed, new_skipped = self.__process_existing_donor_update(validated_donor)
                processed += new_processed
                failed += new_failed
                skipped += new_skipped
                
        logger.info(f"MIABIS on FHIR: Upload of donor resources is done.")
        return {'processed': processed, 'failed': failed, 'skipped': skipped}

    def upload_samples(self):
        logger.info("MIABIS on FHIR: Starting upload of samples...")
        processed = 0
        failed = 0
        skipped = 0
        
        collection_with_new_samples_map = {}
        for sample in self.sample_service.get_all():
            if not isinstance(sample, SampleMiabis):
                logger.error(f"MIABIS on FHIR: sample is not instance of MIABIS on FHIR model, "
                             f"but rather its type is {type(sample)}. Skipping....")
                skipped += 1
                continue
            sample = cast(SampleMiabis, sample)
            try:
                if not self.blaze_client.is_resource_present_in_blaze("Specimen", sample.identifier, "identifier"):

                        sample_fhir_id = self.blaze_client.upload_sample(sample)
                        processed += 1

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
                            try:
                                self.blaze_client.add_diagnoses_to_condition(condition_fhir_id, sample_fhir_id)
                            except Exception as e:
                                logger.debug(f"MIABIS on FHIR: Error adding diagnoses to condition: {e}")
                                failed += 1
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
                        processed += 1
                        patient_fhir_id = self.blaze_client.get_fhir_id("Patient", sample.donor_identifier)
                        condition_fhir_id = self.blaze_client.get_condition_by_patient_fhir_id(patient_fhir_id)
                        try:
                            self.blaze_client.add_diagnoses_to_condition(condition_fhir_id, sample_fhir_id)
                        except Exception as e:
                            logger.debug(f"MIABIS on FHIR: Error adding diagnoses to condition: {e}")
                            failed += 1
                        if sample.sample_collection_id is not None:
                            collection_with_new_samples_map.setdefault(sample.sample_collection_id, []).append(
                                sample_fhir_id)
                    else:
                        skipped += 1
            except (NonExistentResourceException,HTTPError) as err:
                logger.error(f"MIABIS on FHIR: {err}")
                failed += 1

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
        return {'processed': processed, 'failed': failed, 'skipped': skipped}

    def delete_everything(self):
        """Just as name says.DELETES EVERYTHING!!!"""
        biobank = self.biobank_repository.get_biobank()
        logger.info("MIABIS on FHIR:Deleting all resouces from Blaze. It may take a while...")
        self.blaze_client.delete_all_resources(biobank.identifier)
        logger.info("MIABIS on FHIR: Resources deleted.")
        return True

    def __initialize_scheduler(self):
        logger.info("Initializing scheduler....")
        schedule.every().week.do(self.sync)
        logger.info("Scheduler initialized.")

    def run_scheduler(self):
        self.__initialize_scheduler()
        logger.info("Running Scheduler.")
        while True:
            schedule.run_pending()
            time.sleep(1)
