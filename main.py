"""Main module"""
import logging
import sys
import threading

from prometheus_flask_exporter import PrometheusMetrics
from service.blaze_service import BlazeService
from service.mail_service import MailService
from service.manual_run_service import create_api
from service.miabis_blaze_service import MiabisBlazeService
from util.config import get_blaze_url, get_miabis_on_fhir, get_miabis_blaze_url, get_new_file_period_days, get_records_dir_path, get_email_receiver, get_smtp_host, get_smtp_port
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available
from service.configuration_info_service import register_details_routes
from util.service_preparation_utils import prepare_services, prepare_services_miabis

BLAZE_URL = get_blaze_url()
MIABIS_BLAZE_URL = get_miabis_blaze_url()
MIABIS_ON_FHIR = get_miabis_on_fhir()
setup_logger()
logger = logging.getLogger(__name__)
logger.info("Starting FHIR_Module...")

# Prepare standard FHIR services
services = prepare_services()
blaze_service = BlazeService(
    patient_service=services.patient_service,
    condition_service=services.condition_service,
    sample_service=services.sample_service,
    blaze_url=BLAZE_URL,
    sample_collection_repository=services.sample_collection_repository
)

# Prepare MIABIS services if enabled
miabis_blaze_service = None
if MIABIS_ON_FHIR:
    miabis_services = prepare_services_miabis()
    miabis_blaze_service = MiabisBlazeService(
        patient_service=miabis_services.patient_service,
        sample_service=miabis_services.sample_service,
        blaze_url=MIABIS_BLAZE_URL,
        sample_collection_repository=miabis_services.sample_collection_repository,
        biobank_repository=miabis_services.biobank_repository
    )
mail_service = MailService(records_path=get_records_dir_path(), new_file_period=get_new_file_period_days(),
                           smtp_host=get_smtp_host(), smtp_port=get_smtp_port(), email_receiver=get_email_receiver())
if (MIABIS_ON_FHIR and miabis_blaze_service is not None):
    app = create_api(blaze_service, miabis_blaze_service)
else:
    app = create_api(blaze_service)

register_details_routes(app)

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
    if MIABIS_ON_FHIR and miabis_blaze_service is not None:
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
