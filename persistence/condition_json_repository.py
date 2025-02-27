import json
import logging
import os
import csv
import re
from json import JSONDecodeError
from typing import List

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from util.custom_logger import setup_logger
from dateutil import parser as date_parser
from dateutil.parser import ParserError

from util.sample_util import extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class ConditionJsonRepository(ConditionRepository):
    """ Class for handling condition persistence in Csv files """

    def __init__(self, records_path: str, condition_parsing_map: dict):
        self._dir_path = records_path
        self._sample_parsing_map = condition_parsing_map
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> List[Condition]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".json"):
                yield from self.__extract_condition_from_csv_file(dir_entry)

    def __extract_condition_from_csv_file(self, dir_entry: os.DirEntry) -> Condition:
        with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
            try:
                conditions_json = json.load(json_file)
            except JSONDecodeError:
                logger.error("Biobank file does not have a correct JSON format. Exiting...")
                return

            for condition_json in conditions_json:
                try:
                    diagnosis_field = condition_json.get(self._sample_parsing_map.get("icd-10_code"))
                    if diagnosis_field is None:
                        logger.error("No ICD-10 code field found in the csv file. Skipping...")
                        continue
                    diagnoses = extract_all_diagnosis(diagnosis_field)
                    patient_id = str(condition_json.get(self._sample_parsing_map.get("patient_id")))
                    diagnosis_datetime = condition_json.get(self._sample_parsing_map.get("diagnosis_date"))
                    if diagnosis_datetime is not None:
                        try:
                            diagnosis_datetime = date_parser.parse(diagnosis_datetime)
                            diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
                        except ParserError:
                            logger.info(
                                f"Error parsing date for condition for patient with id {patient_id} "
                                f"while parsing diagnosis datetime with value {diagnosis_datetime}. "
                                f"Please make sure the date is in a valid format."
                            )
                            return
                    for diagnosis in diagnoses:
                        condition = Condition(patient_id=patient_id, icd_10_code=diagnosis,
                                              diagnosis_datetime=diagnosis_datetime)
                        yield condition
                except TypeError as err:
                    logger.error(f"{err} Skipping...")
                    continue
