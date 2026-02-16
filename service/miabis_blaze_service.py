import threading
import time
from typing import cast

import requests
import schedule
from blaze_client import BlazeClient, NonExistentResourceException
import logging
import json

from requests import HTTPError

from exception.wrong_parsing_map import WrongParsingMapException
from model.miabis.collection_miabis import CollectionMiabis
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.miabis.sample_miabis import SampleMiabis
from persistence.biobank_repository import BiobankRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from service.blaze_service_interface import BlazeServiceInterface

from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import get_miabis_blaze_auth
from util.custom_logger import setup_logger
from util.metrics import get_metrics_for_service
from util.service_preparation_utils import prepare_services_miabis

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
        self.blaze_client = BlazeClient(blaze_url=blaze_url, blaze_username=get_miabis_blaze_auth()[0], blaze_password=get_miabis_blaze_auth()[1])
        self.patient_service = patient_service
        self.sample_service = sample_service
        self.sample_collection_repository = sample_collection_repository
        self.biobank_repository = biobank_repository
        self.metrics = get_metrics_for_service('miabis-blaze')
        self._scheduler_thread = None

    def _refresh_services(self) -> bool:
        """
        Refresh services and repositories to handle file format changes.
        This allows the sync to adapt to changes in data source format (CSV, JSON, XML).
        
        Returns:
            bool: True if services were successfully refreshed, False otherwise
        """
        logger.info("MIABIS on FHIR: Refreshing services to detect any file format changes...")
        services = prepare_services_miabis()
        self.patient_service = services.patient_service
        self.sample_service = services.sample_service
        self.sample_collection_repository = services.sample_collection_repository
        self.biobank_repository = services.biobank_repository
        
        if self.patient_service is None:
            logger.warning("MIABIS services not initialized: parsing map configuration is missing or invalid.")
            return False
        
        logger.debug("MIABIS on FHIR: Services refreshed successfully.")
        # Ensure scheduler is still running after refresh
        self.ensure_scheduler_running()
        return True

    def sync(self):
        if self.metrics:
            self.metrics.start_sync()
        
        try:
            if not self._refresh_services():
                error_msg = "MIABIS sync failed: Mapping files are misconfigured. Please check your parsing map configuration."
                sync_logger.error(error_msg)
                if self.metrics:
                    self.metrics.set_metric('last_sync_error', error_msg)
                return

            biobank_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
            collection_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
            pat_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
            samp_summary = {'processed': 0, 'failed': 0, 'skipped': 0}
            if self.metrics:
                self.metrics.set_sync_phase(1)  # Phase 1: Biobank and Collections
            biobank_collection_summary = self.sync_biobank_and_collections()
            biobank_summary = biobank_collection_summary['biobank']
            collection_summary = biobank_collection_summary['collections']
            
            if self.metrics:
                self.metrics.set_sync_phase(2)  # Phase 2: Patients
            pat_summary = self.upload_patients()
            
            if self.metrics:
                self.metrics.set_sync_phase(4)  # Phase 4: Specimens (skipping 3 as MIABIS handles conditions differently)
            samp_summary, condition_summary = self.upload_samples()

            if self.metrics:
                self.metrics.set_metric('last_sync_timestamp', time.time())

            sync_summary_obj = {
                'patients': pat_summary,
                'specimens': samp_summary,
                'conditions': condition_summary,
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
                'conditions': condition_summary,
                'biobank': biobank_summary,
                'collections': collection_summary,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'success': False,
                'error_message': str(e)
            }
            sync_logger.info(json.dumps({'sync_summary': sync_summary_obj}))
        finally:
            # Always ensure sync state is cleaned up
            if self.metrics:
                self.metrics.end_sync()

    def __create_sync_summary(self) -> dict:
        """Create empty sync summary structure for biobank and collections."""
        return {
            'biobank': {'processed': 0, 'failed': 0, 'skipped': 0},
            'collections': {'processed': 0, 'failed': 0, 'skipped': 0}
        }

    def __upload_biobank(self, biobank, summary: dict) -> bool:
        """
        Upload or skip biobank based on its presence in Blaze.
        Returns True if successful, False if error occurred.
        """
        try:
            if not self.blaze_client.is_resource_present_in_blaze("Organization", biobank.identifier, "identifier"):
                logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank.identifier} not present in blaze. uploading...")
                self.blaze_client.upload_biobank(biobank)
                summary['biobank']['processed'] += 1
                logger.info(f"MIABIS on FHIR: Successfully uploaded biobank.")
            else:
                logger.info(f"MIABIS on FHIR: Biobank with identifier {biobank} is already present in blaze.")
                summary['biobank']['skipped'] += 1
            return True
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to the blaze server!")
            summary['biobank']['failed'] += 1
            return False
        except (ValueError, KeyError, TypeError, HTTPError) as err:
            logger.error(f"{err}")
            summary['biobank']['failed'] += 1
            return False

    def __validate_collection_type(self, collection) -> CollectionMiabis | None:
        """Validate that collection is of correct type and return cast collection or None if invalid."""
        if not isinstance(collection, CollectionMiabis):
            logger.error(
                f"MIABIS ON FHIR: collection is not instance of MIABIS on FHIR model, but rather its type is {type(collection)} Skipping...")
            return None
        return cast(CollectionMiabis, collection)

    def __process_single_collection(self, collection: CollectionMiabis, summary: dict) -> None:
        """Process upload of a single collection and update summary."""
        if self.blaze_client.is_resource_present_in_blaze("Organization", collection.identifier, "identifier"):
            summary['collections']['skipped'] += 1
            return

        try:
            logger.debug(f"MIABIS on FHIR: Collection with identifier {collection.identifier} is not present. Uploading...")
            self.blaze_client.upload_collection(collection)
            summary['collections']['processed'] += 1
            logger.debug(f"MIABIS on FHIR: Successfully uploaded collection with identifier {collection.identifier}")
        except Exception as e:
            logger.error(f"MIABIS on FHIR: Error uploading collection {collection.identifier}: {e}")
            summary['collections']['failed'] += 1

    def __upload_collections(self, summary: dict) -> None:
        """Upload all collections from repository."""
        logger.info(f"MIABIS on FHIR: Starting upload of collections")
        
        for collection in self.sample_collection_repository.get_all():
            validated_collection = self.__validate_collection_type(collection)
            if validated_collection is None:
                summary['collections']['skipped'] += 1
            else:
                self.__process_single_collection(validated_collection, summary)
            
            if self.metrics:
                self.metrics.increment_sync_progress('collections')
        
        logger.info(f"MIABIS on FHIR: Collections sync complete: {summary['collections']['processed']} processed, {summary['collections']['failed']} failed, {summary['collections']['skipped']} skipped")

    def sync_biobank_and_collections(self):
        summary = self.__create_sync_summary()
        biobank = self.biobank_repository.get_biobank()
        
        biobank_success = self.__upload_biobank(biobank, summary)
        
        if biobank_success:
            self.__upload_collections(summary)
        
        logger.info(f"MIABIS on FHIR: Sync of biobank and collection resources is done.")
        return summary

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
                if self.metrics:
                    self.metrics.increment_sync_progress('patients')
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
            
            if self.metrics:
                self.metrics.increment_sync_progress('patients')
                
        logger.info(f"MIABIS on FHIR: Upload of donor resources is done.")
        logger.info(f"MIABIS on FHIR: Patients sync complete: {processed} processed, {failed} failed, {skipped} skipped")
        return {'processed': processed, 'failed': failed, 'skipped': skipped}

    def upload_samples(self):
        logger.info("MIABIS on FHIR: Starting upload of samples...")
        processed_samples = 0
        failed_samples = 0
        skipped_samples = 0

        processed_conditions = 0
        failed_conditions = 0
        skipped_conditions = 0
        collection_with_new_samples_map = {}
        for sample in self.sample_service.get_all():
            if not isinstance(sample, SampleMiabis):
                logger.error(f"MIABIS on FHIR: sample is not instance of MIABIS on FHIR model, "
                             f"but rather its type is {type(sample)}. Skipping....")
                skipped_samples += 1
                if self.metrics:
                    self.metrics.increment_sync_progress('specimens')
                continue
            sample = cast(SampleMiabis, sample)
            try:
                if not self.blaze_client.is_resource_present_in_blaze("Specimen", sample.identifier, "identifier"):

                        sample_fhir_id = self.blaze_client.upload_sample(sample)

                        logger.debug(f"MIABIS on FHIR: Successfully uploaded sample with id {sample.identifier}")
                        patient_fhir_id = self.blaze_client.get_fhir_id("Patient", sample.donor_identifier)

                        if self.metrics:
                            self.metrics.increment_sync_progress('conditions')
                        if not self.blaze_client.is_resource_present_in_blaze("Condition", patient_fhir_id,
                                                                              "subject"):
                            logger.debug(
                                f"MIABIS on FHIR: Condition for patient : {sample.donor_identifier} is not present. Uploading new condition")

                            try:
                                self.blaze_client.upload_condition(sample.condition)
                                processed_conditions += 1
                            except Exception as e:
                                logger.error(f"MIABIS on FHIR: Error uploading condition {sample.condition.icd_10_code}: {e}")
                                failed_conditions += 1
                            logger.debug(f"MIABIS on FHIR: Succesfully uploaded new Condition")
                        else:
                            skipped_conditions += 1
                            condition_fhir_id = self.blaze_client.get_condition_by_patient_fhir_id(patient_fhir_id)
                            self.blaze_client.add_diagnoses_to_condition(condition_fhir_id, sample_fhir_id)
                        if sample.sample_collection_id is not None:
                            collection_with_new_samples_map.setdefault(sample.sample_collection_id, []).append(
                                sample_fhir_id)

                        processed_samples += 1
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

                        processed_samples += 1
                    else:
                        skipped_samples += 1
            except (NonExistentResourceException, HTTPError) as err:
                logger.error(f"MIABIS on FHIR: {err}")
                failed_samples += 1
            
            if self.metrics:
                self.metrics.increment_sync_progress('specimens')

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
        logger.info(f"MIABIS on FHIR: Samples sync complete: {processed_samples} processed, {failed_samples} failed, {skipped_samples} skipped")
        return {'processed': processed_samples, 'failed': failed_samples, 'skipped': skipped_samples}, {'processed': processed_conditions, 'failed': failed_conditions, 'skipped': skipped_conditions}

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

    def start_scheduler(self):
        """Start the scheduler in a daemon thread if not already running."""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            logger.info("Starting MIABIS scheduler thread...")
            self._scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self._scheduler_thread.start()
            logger.info("MIABIS scheduler thread started.")
        else:
            logger.debug("MIABIS scheduler thread is already running.")

    def ensure_scheduler_running(self):
        """Ensure scheduler is running, start it if needed."""
        self.start_scheduler()
