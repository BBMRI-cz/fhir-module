import json
import logging
import os
from json import JSONDecodeError
from typing import Callable, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from util.custom_logger import setup_logger
from util.sample_util import extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class ConditionJsonRepository(ConditionRepository):
    """ Class for handling condition persistence in Csv files """

    def __init__(self, records_path: str, condition_parsing_map: dict):
        super().__init__(records_path)
        self._sample_parsing_map = condition_parsing_map
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> Generator[Condition, None, None]:
        with os.scandir(self._dir_path) as entries:
            for dir_entry in entries:
                if dir_entry.name.lower().endswith(".json"):
                    yield from self.__extract_condition_from_json_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".json", self.__validate_conditions_from_json_file
    
    def __extract_condition_from_json_file(self, dir_entry: os.DirEntry) -> Condition:
        try:
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
        except OSError as e:
            logger.debug(f"Error while opening file {dir_entry.name}: {e}")
            logger.info(f"Error while opening file {dir_entry.name} [Skipping...]")
            return

    def __validate_json_diagnosis_field(self, condition_json: dict, validation_errors: list) -> str | None:
        """Extract and validate the diagnosis field from JSON."""
        diagnosis_field = condition_json.get(self._sample_parsing_map.get("icd-10_code"))
        if diagnosis_field is None:
            validation_errors.append(ValueError("No ICD-10 code field found in the JSON file"))
        return diagnosis_field

    def __validate_json_patient_id_field(self, condition_json: dict, validation_errors: list) -> str | None:
        """Extract and validate the patient ID field from JSON."""
        patient_id = condition_json.get(self._sample_parsing_map.get("patient_id"))
        if patient_id is None:
            validation_errors.append(ValueError("No patient ID field found in the JSON file"))
        return patient_id

    def __parse_json_diagnosis_datetime(self, condition_json: dict, validation_errors: list):
        """Parse the optional diagnosis datetime field from JSON."""
        diagnosis_datetime = condition_json.get(self._sample_parsing_map.get("diagnosis_date"))
        if diagnosis_datetime is not None:
            try:
                diagnosis_datetime = date_parser.parse(diagnosis_datetime)
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                validation_errors.append(ParserError("Diagnosis date parsing error"))
        return diagnosis_datetime

    def __validate_json_diagnoses(self, diagnosis_field: str | None, patient_id: str | None, 
                                  validation_errors: list) -> list[str]:
        """Extract and validate diagnoses from the diagnosis field."""
        diagnoses = []
        if diagnosis_field is not None:
            diagnoses = extract_all_diagnosis(diagnosis_field)
        
        if not diagnoses:
            validation_errors.append(
                ValueError(f"No correct diagnosis has been found for patient with id {str(patient_id)}")
            )
        
        return diagnoses

    def __validate_conditions_from_json_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
                try:
                    conditions_json = json.load(json_file)
                except JSONDecodeError:
                    errors.append(f"File {dir_entry.name} - does not have a correct JSON format. Exiting...")
                    return errors

                condition_index = 0
                for condition_json in conditions_json:
                    validation_errors = []
                    
                    # Validate mandatory fields
                    diagnosis_field = self.__validate_json_diagnosis_field(condition_json, validation_errors)
                    patient_id = self.__validate_json_patient_id_field(condition_json, validation_errors)
                    
                    # Parse optional diagnosis datetime
                    _ = self.__parse_json_diagnosis_datetime(condition_json, validation_errors)
                    
                    # Extract and validate diagnoses
                    _ = self.__validate_json_diagnoses(diagnosis_field, patient_id, validation_errors)

                    # If there are validation errors, add them all together
                    if validation_errors:
                        for exc in validation_errors:
                            errors.append(f"File {dir_entry.name} - Condition (index {condition_index}): {exc}")
                    
                    condition_index += 1
        except OSError as e:
            errors.append(f"Error while opening file {dir_entry.name}: {e}")
            return errors

        return errors