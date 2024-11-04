import json
import logging
import sys
from json import JSONDecodeError
from typing import Generator

from model.interface.collection_interface import CollectionInterface
from model.miabis.collection_miabis import CollectionMiabis
from model.sample_collection import SampleCollection
from persistence.sample_collection_repository import SampleCollectionRepository
from util.config import SAMPLE_COLLECTIONS_PATH
from util.custom_logger import setup_logger, logger


class SampleCollectionJSONRepository(SampleCollectionRepository):
    setup_logger()
    logger = logging.getLogger()

    def __init__(self, collections_json_file_path: str, miabis_on_fhir_model: bool = False):
        self._collections_json_file_path = collections_json_file_path
        self._miabis_on_fhir_model = miabis_on_fhir_model

    def get_all(self) -> Generator[CollectionInterface, None, None]:
        with open(SAMPLE_COLLECTIONS_PATH) as json_file:
            try:
                collections_json = json.load(json_file)
                for entry in collections_json:
                    collection = self.__build_sample_collection(entry)
                    yield collection
            except JSONDecodeError:
                logger.error("Material type map does not have correct JSON format. Exiting.")
                sys.exit()

    def __build_sample_collection(self, collection_json: dict) -> CollectionInterface:
        if self._miabis_on_fhir_model:
            collection = CollectionMiabis(identifier=collection_json.get("identifier"),
                                          name=collection_json.get("name"),
                                          managing_biobank_id=collection_json.get("managing_biobank_id"),
                                          contact_name=collection_json.get("contact_name"),
                                          contact_surname=collection_json.get("contact_surname"),
                                          contact_email=collection_json.get("contact_email"),
                                          country=collection_json.get("country"),
                                          alias=collection_json.get("alias"),
                                          url=collection_json.get("url"),
                                          description=collection_json.get("description"),
                                          dataset_type=collection_json.get("dataset_type"),
                                          sample_source=collection_json.get("sample_source"),
                                          sample_collection_setting=collection_json.get("sample_collection_setting"),
                                          collection_design=collection_json.get("collection_design"),
                                          use_and_access_conditions=collection_json.get("use_and_Acess_conditions"),
                                          publications=collection_json.get("publications"),
                                          material_types=collection_json.get("material_types", ["Other"]))
        else:
            collection = SampleCollection(identifier=collection_json.get("identifier"))
        return collection
