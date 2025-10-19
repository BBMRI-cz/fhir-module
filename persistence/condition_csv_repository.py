from collections.abc import Callable
import csv
import logging
import os
from datetime import datetime
from typing import Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from util.custom_logger import setup_logger
from util.sample_util import extract_all_diagnosis
from util.config import get_csv_separator

setup_logger()
logger = logging.getLogger()

class ConditionCsvRepository(ConditionRepository):
    """ Class for handling condition persistence in Csv files """

    def __init__(self, records_path: str, separator: str, condition_parsing_map: dict):
        super().__init__(records_path)
        self._dir_path = records_path
        self.separator = separator
        self._condition_parsing_map = condition_parsing_map
        self._fields_dict = {}
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> Generator[Condition, None, None]:
        dir_entries = list(os.scandir(self._dir_path))
        for dir_entry in dir_entries:
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_condition_from_csv_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()
        self._separator = get_csv_separator()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".csv", self.__validate_conditions_from_csv_file  

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

    def __validate_conditions_from_csv_file(self, dir_entry: os.DirEntry) ->  list[str]:
        errors = []
        try:
            with open(dir_entry, "r") as file_content:
                reader = csv.reader(file_content, delimiter=self.separator)
                self._fields_dict = {}
                fields = next(reader)
                for i, field in enumerate(fields):
                    self._fields_dict[field] = i
                row_index = 1
                for row in reader:
                    try:
                        self.__build_conditions(row, is_validation=True)
                    except ExceptionGroup as eg:
                        for exc in eg.exceptions:
                            errors.append(f"Condition (row {row_index}): {exc}")
                    except TypeError as err:
                        errors.append(f"Condition (row {row_index}): {err}")
                    finally:
                        row_index += 1
        except OSError as e:
            return [f"Error while opening file {dir_entry.name}: {e}"]

        return errors

    def __validate_diagnosis_field(self, validation_errors: list | None) -> int | None:
        """Extract and validate the diagnosis field index."""
        diagnosis_field = self._fields_dict.get(self._condition_parsing_map.get("icd-10_code"))
        if diagnosis_field is None:
            error_message = "No ICD-10 code field found in the csv file. Skipping..."
            logger.error(error_message)
            if validation_errors is not None:
                validation_errors.append(ValueError(error_message))
        return diagnosis_field

    def __validate_patient_id_field(self, data: list[str], validation_errors: list | None) -> str | None:
        """Extract and validate the patient ID field."""
        patient_id_field = self._fields_dict.get(self._condition_parsing_map.get("patient_id"))
        if patient_id_field is None:
            error_message = "No patient ID field found in the csv file. Skipping..."
            logger.error(error_message)
            if validation_errors is not None:
                validation_errors.append(ValueError(error_message))
            return None
        return data[patient_id_field]

    def __extract_diagnoses(self, data: list[str], diagnosis_field: int, patient_id: str, 
                           validation_errors: list | None) -> list[str]:
        """Extract diagnoses from the data row."""
        diagnoses = []
        if diagnosis_field is not None:
            diagnoses = extract_all_diagnosis(data[diagnosis_field])
        
        if not diagnoses:
            exception = ValueError(f"No correct diagnosis has been found for patient with id {patient_id}")
            if validation_errors is not None:
                validation_errors.append(exception)
        
        return diagnoses

    def __parse_diagnosis_datetime(self, data: list[str], patient_id: str, 
                                   validation_errors: list | None) -> datetime | None:
        """Parse the optional diagnosis datetime field."""
        diagnosis_datetime = None
        diagnosis_datetime_field = self._fields_dict.get(self._condition_parsing_map.get("diagnosis_date"))
        
        if diagnosis_datetime_field is not None:
            try:
                diagnosis_datetime = date_parser.parse(data[diagnosis_datetime_field])
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                exception = ParserError(
                    f"Error parsing date for condition for patient with id {patient_id} "
                    f"while parsing diagnosis datetime with value {data[diagnosis_datetime_field]}. "
                    f"Please make sure the date is in a valid format."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise exception
        
        return diagnosis_datetime

    def __create_condition_objects(self, diagnoses: list[str], patient_id: str, 
                                   diagnosis_datetime) -> list[Condition]:
        """Create Condition objects from diagnoses."""
        parsed_conditions = []
        for diagnosis in diagnoses:
            condition = Condition(patient_id=patient_id, icd_10_code=diagnosis,
                                  diagnosis_datetime=diagnosis_datetime)
            parsed_conditions.append(condition)
        return parsed_conditions

    def __build_conditions(self, data: list[str], is_validation: bool = False) -> list[Condition]:
        validation_errors = []

        # Validate mandatory fields
        diagnosis_field = self.__validate_diagnosis_field(validation_errors)
        patient_id = self.__validate_patient_id_field(data, validation_errors)
        
        if diagnosis_field is None or patient_id is None:
            if is_validation and validation_errors:
                raise ExceptionGroup("Validation errors", validation_errors)
            return []

        # Extract and validate diagnoses
        diagnoses = self.__extract_diagnoses(data, diagnosis_field, patient_id, validation_errors)
        
        # Parse optional diagnosis datetime
        diagnosis_datetime = self.__parse_diagnosis_datetime(data, patient_id, validation_errors)

        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)

        # Create condition objects
        return self.__create_condition_objects(diagnoses, patient_id, diagnosis_datetime)
