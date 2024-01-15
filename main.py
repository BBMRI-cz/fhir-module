"""Main module"""
import logging
import sys
from service.blaze_service import BlazeService
from util.config import BLAZE_URL
from util.custom_logger import setup_logger
from util.http_util import is_endpoint_available
from persistence.factories.factory_util import get_repository_factory

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting FHIR_Module...")
    if is_endpoint_available(endpoint_url=BLAZE_URL, wait_time=10, max_attempts=5):
        repository_factory = get_repository_factory()
        blaze_service = BlazeService(repository_factory=repository_factory, blaze_url=BLAZE_URL)
        blaze_service.sync()
    else:
        logger.error("Exiting FHIR_Module.")
        sys.exit()
