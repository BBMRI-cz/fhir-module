"""Main module"""
import logging
import sys
import threading

from prometheus_flask_exporter import PrometheusMetrics
from persistence.factories.factory_util import get_repository_factory
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.mail_service import MailService
from service.manual_run_service import create_api
from service.miabis_blaze_service import MiabisBlazeService
from service.patient_service import PatientService
from service.sample_service import SampleService
from util.config import BLAZE_URL, MIABIS_BLAZE_URL, RECORDS_DIR_PATH, NEW_FILE_PERIOD_DAYS, SMTP_HOST, SMTP_PORT, \
    EMAIL_RECEIVER, MIABIS_ON_FHIR
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available
from util.metrics import get_metrics_for_service

setup_logger()
logger = logging.getLogger(__name__)
logger.info("Starting FHIR_Module...")

repository_factory = get_repository_factory()
patient_service = PatientService(repository_factory.create_sample_donor_repository())
condition_service = ConditionService(repository_factory.create_condition_repository())
sample_service = SampleService(repository_factory.create_sample_repository())
sample_collection_repository = repository_factory.create_sample_collection_repository()
blaze_service = BlazeService(patient_service=patient_service, condition_service=condition_service,
                             sample_service=sample_service, blaze_url=BLAZE_URL,
                             sample_collection_repository=sample_collection_repository)
miabis_blaze_service = None
if MIABIS_ON_FHIR:
    patient_service_miabis = PatientService(repository_factory.create_sample_donor_repository(True))
    sample_service_miabis = SampleService(repository_factory.create_sample_repository(True))
    sample_collection_repository_miabis = repository_factory.create_sample_collection_repository(True)
    biobank_repository = repository_factory.create_biobank_repository()
    miabis_blaze_service = MiabisBlazeService(patient_service=patient_service_miabis,
                                              sample_service=sample_service_miabis, blaze_url=MIABIS_BLAZE_URL,
                                              sample_collection_repository=sample_collection_repository_miabis,
                                              biobank_repository=biobank_repository)
mail_service = MailService(records_path=RECORDS_DIR_PATH, new_file_period=NEW_FILE_PERIOD_DAYS,
                           smtp_host=SMTP_HOST, smtp_port=SMTP_PORT, email_receiver=EMAIL_RECEIVER)
app = create_api(blaze_service, miabis_blaze_service)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

if is_endpoint_available(endpoint_url=BLAZE_URL, wait_time=10, max_attempts=5):
    if MIABIS_ON_FHIR:
        if not is_endpoint_available(endpoint_url=MIABIS_BLAZE_URL, wait_time=10, max_attempts=5):
            logger.error("Exiting FHIR_Module.")
            sys.exit()
    # validator_factory = get_validator_factory()
    # validator = validator_factory.create_validator()
    # try:
    #     validator.validate()
    # except (NoFilesProvidedException, NonexistentAttributeParsingMapException, WrongParsingMapException):
    #     logger.error("Incorrect parsing map and/or file structure. Exiting FHIR_module.")
    #     sys.exit()
    blaze_service.sync()
    if MIABIS_ON_FHIR:
        miabis_blaze_service.sync()
        scheduler_miabis_thread = threading.Thread(target=miabis_blaze_service.run_scheduler, daemon=True)
        scheduler_miabis_thread.start()
    scheduler_thread = threading.Thread(target=blaze_service.run_scheduler, daemon=True)
    scheduler_mail_thread = threading.Thread(target=mail_service.run_scheduler, daemon=True)
    scheduler_mail_thread.start()
    scheduler_thread.start()
else:
    logger.error("Exiting FHIR_Module.")
    sys.exit()
