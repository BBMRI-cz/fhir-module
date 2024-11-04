import json
import logging
import sys
from json import JSONDecodeError

from miabis_model import Biobank

from persistence.biobank_repository import BiobankRepository
from util.custom_logger import setup_logger, logger


class BiobankJSONRepository(BiobankRepository):
    setup_logger()
    logger = logging.getLogger()

    def __init__(self, biobank_json_file_path: str):
        self._biobank_json_file_path = biobank_json_file_path

    def get_biobank(self) -> Biobank:
        with open(self._biobank_json_file_path) as json_file:
            try:
                biobank_json = json.load(json_file)
                biobank = Biobank(identifier=biobank_json.get("identifier"),
                                  name=biobank_json.get("name"),
                                  alias=biobank_json.get("alias"),
                                  country=biobank_json.get("country"),
                                  contact_name=biobank_json.get("contact_name"),
                                  contact_surname=biobank_json.get("contact_surname"),
                                  contact_email=biobank_json.get("contact_email"),
                                  infrastructural_capabilities=biobank_json.get("infrastructural_capabilities"),
                                  organisational_capabilities=biobank_json.get("organisational_capabilities"),
                                  bioprocessing_and_analysis_capabilities=biobank_json.get(
                                      "bioprocessing_and_analysis_capabilities"),
                                  quality__management_standards=biobank_json.get("quality_management_standards"),
                                  juristic_person=biobank_json.get("juristic_person"),
                                  description=biobank_json.get("description"))
                return biobank
            except JSONDecodeError:
                logger.error("Biobank file does not have a correct JSON format. Exiting...")
                sys.exit()
