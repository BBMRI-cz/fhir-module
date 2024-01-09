import logging
import os
import pandas as pd
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
            if dir_entry.name.endswith(".csv"):
                yield from self.__extract_condition_from_csv_file(dir_entry)

    def __extract_condition_from_csv_file(self, dir_entry: os.DirEntry) -> Condition:
        file_content = pd.read_csv(dir_entry, sep=self.separator, dtype=str)
        try:
            for _, row in file_content.iterrows():
                try:
                    diagnosis = self.__extract_first_diagnosis(self, row[self._sample_parsing_map.get("icd-10_code")])
                    patient_id = row[self._sample_parsing_map.get("patient_id")]
                    condition = Condition(patient_id=patient_id, icd_10_code=diagnosis)
                    yield condition
                except TypeError:
                    logger.info("Parsed string is not a valid ICD-10 code. Skipping...")
                    return
        except TypeError:
            return

    @staticmethod
    def __extract_first_diagnosis(self, diagnosis_str: str):
        """Extracts only the first diagnosis, in case the file has multiple diagnosis"""
        if ',' in diagnosis_str:
            return diagnosis_str.split(',')[0].strip()
        else:
            return diagnosis_str.strip()