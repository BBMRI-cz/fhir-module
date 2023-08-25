import json
import logging
import sys
from json import JSONDecodeError
from typing import Generator

from model.sample_collection import SampleCollection
from persistence.sample_collection_repository import SampleCollectionRepository
from util.config import SAMPLE_COLLECTIONS_PATH
from util.custom_logger import setup_logger, logger


class SampleCollectionJSONRepository(SampleCollectionRepository):
    setup_logger()
    logger = logging.getLogger()

    def __init__(self, collections_json_file_path: str):
        self._collections_json_file_path = collections_json_file_path

    def get_all(self) -> Generator[SampleCollection, None, None]:
        with open(SAMPLE_COLLECTIONS_PATH) as json_file:
            try:
                collections_json = json.load(json_file)
                for entry in collections_json:
                    yield SampleCollection(identifier=entry["identifier"])
            except JSONDecodeError:
                logger.error("Material type map does not have correct JSON format. Exiting.")
                sys.exit()
