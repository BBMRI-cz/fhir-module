import logging
import os
import csv
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
                        return
                    diagnosis = self.__extract_first_diagnosis(self, row[diagnosis_field])
                    patient_id = row[fields_dict[self._sample_parsing_map.get("patient_id")]]
                    condition = Condition(patient_id=patient_id, icd_10_code=diagnosis)
                    yield condition
                except TypeError:
                    logger.info("Parsed string is not a valid ICD-10 code. Skipping...")
                    return

    @staticmethod
    def __extract_first_diagnosis(self, diagnosis_str: str):
        """Extracts only the first diagnosis, in case the file has multiple diagnosis"""
        if ',' in diagnosis_str:
            return diagnosis_str.split(',')[0].strip()
        else:
            return diagnosis_str.strip()
