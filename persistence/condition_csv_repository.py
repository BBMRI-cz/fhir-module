import logging
import os
import csv
import re
from typing import List

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class ConditionCsvRepository(ConditionRepository):
    """ Class for handling condition persistence in Csv files """

    def __init__(self, records_path: str, separator: str, condition_parsing_map: dict):
        self._dir_path = records_path
        self.separator = separator
        self._sample_parsing_map = condition_parsing_map
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> List[Condition]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_condition_from_csv_file(dir_entry)

    def __extract_condition_from_csv_file(self, dir_entry: os.DirEntry) -> Condition:
        fields_dict: dict = {}
        with open(dir_entry, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self.separator)
            fields = next(reader)
            for i, field in enumerate(fields):
                fields_dict[field] = i
            for row in reader:
                try:
                    diagnosis_field = fields_dict.get(self._sample_parsing_map.get("icd-10_code"))
                    if diagnosis_field is None:
                        logger.error("No ICD-10 code field found in the csv file. Skipping...")
                        continue
                    diagnoses = self.__extract_all_diagnosis(row[diagnosis_field])
                    patient_id = row[fields_dict[self._sample_parsing_map.get("patient_id")]]
                    for diagnosis in diagnoses:
                        condition = Condition(patient_id=patient_id, icd_10_code=diagnosis)
                        yield condition
                except TypeError as err:
                    logger.error(f"{err} Skipping...")
                    continue

    @staticmethod
    def __extract_all_diagnosis(diagnosis_str: str) -> list[str]:
        """Extract all diagnosis from a string"""
        pattern = r'\b[A-Z][0-9]{2}(?:\.)?(?:[0-9]{1,2})?\b'
        return re.findall(pattern, diagnosis_str)
