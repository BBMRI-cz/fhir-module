import csv
import logging
import os
from typing import Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from util.custom_logger import setup_logger
from util.sample_util import extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class ConditionCsvRepository(ConditionRepository):
    """ Class for handling condition persistence in Csv files """

    def __init__(self, records_path: str, separator: str, condition_parsing_map: dict):
        self._dir_path = records_path
        self.separator = separator
        self._sample_parsing_map = condition_parsing_map
        self._fields_dict = {}
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> Generator[Condition, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_condition_from_csv_file(dir_entry)

    def __extract_condition_from_csv_file(self, dir_entry: os.DirEntry) -> Condition:
        try:
            with open(dir_entry, "r") as file_content:
                reader = csv.reader(file_content, delimiter=self.separator)
                self._fields_dict = {}
                fields = next(reader)
                for i, field in enumerate(fields):
                    self._fields_dict[field] = i
                for row in reader:
                    try:
                        conditions = self.__build_conditions(row)
                        if conditions is None:
                            continue
                        for condition in conditions:
                            yield condition
                    except TypeError as err:
                        logger.error(f"{err} Skipping...")
                        continue
        except OSError as e:
            logger.debug(f"Error while opening file {dir_entry.name}: {e}")
            logger.info(f"Error while opening file {dir_entry.name} [Skipping...]")
            return

    def __build_conditions(self, data: list[str]):
        parsed_conditions = []
        diagnosis_field = self._fields_dict.get(self._sample_parsing_map.get("icd-10_code"))
        if diagnosis_field is None:
            logger.error("No ICD-10 code field found in the csv file. Skipping...")
            return
        diagnoses = extract_all_diagnosis(data[diagnosis_field])
        patient_id = data[self._fields_dict[self._sample_parsing_map.get("patient_id")]]
        diagnosis_datetime = None
        diagnosis_datetime_field = self._fields_dict.get(self._sample_parsing_map.get("diagnosis_date"))
        if diagnosis_datetime_field is not None:
            try:
                diagnosis_datetime = date_parser.parse(data[diagnosis_datetime_field])
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                logger.info(
                    f"Error parsing date for condition for patient with id {patient_id} "
                    f"while parsing diagnosis datetime with value {data[diagnosis_datetime_field]}. "
                    f"Please make sure the date is in a valid format."
                )
                return
        for diagnosis in diagnoses:
            condition = Condition(patient_id=patient_id, icd_10_code=diagnosis,
                                  diagnosis_datetime=diagnosis_datetime)
            parsed_conditions.append(condition)
        return parsed_conditions
