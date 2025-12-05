"""Module containing classes tied to condition persistence in XML files"""
import logging
import os
from typing import Callable, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError
from glom import glom

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class ConditionXMLRepository(ConditionRepository):
    """Class for handling condition persistence in XML files"""

    def __init__(self, records_path: str, condition_parsing_map: dict):
        super().__init__(records_path)
        self._sample_parsing_map = condition_parsing_map
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> Generator[Condition, None, None]:
        dir_entries = list(os.scandir(self._dir_path))
        for dir_entry in dir_entries:
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_condition_from_xml_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".xml", self.__validate_conditions_from_xml_file

    def __extract_condition_from_xml_file(self, dir_entry: os.DirEntry) -> Condition:
        """Extracts Condition from an XML file"""
        try:
            file_content = parse_xml_file(dir_entry)
        except WrongXMLFormatError:
            logger.info(f"Wrong XLM format of file: {dir_entry.name} [Skipping...]")
            return
        try:
            for diagnosis in glom(file_content, self._sample_parsing_map.get("icd-10_code")):
                patient_id = glom(file_content, self._sample_parsing_map.get("patient_id"))
                try:
                    diagnosis_datetime_path = self._sample_parsing_map.get("diagnosis_date")
                    if diagnosis_datetime_path is None or diagnosis_datetime_path == "":
                        diagnosis_datetime = None
                    else:
                        diagnosis_datetime = glom(file_content, diagnosis_datetime_path, default=None)

                    if diagnosis_datetime is not None and len(diagnosis_datetime) == 0:
                        diagnosis_datetime = None
                    if diagnosis_datetime is not None:
                        try:
                            diagnosis_datetime = date_parser.parse(diagnosis_datetime[0])
                            diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
                        except ParserError:
                            logger.info(
                                f"Error parsing date for condition for patient with id {patient_id} "
                                f"while parsing diagnosis datetime with value {diagnosis}. "
                                f"Please make sure the date is in a valid format."
                                f"Skipping ...")
                            return
                    condition = Condition(patient_id=patient_id,
                                          icd_10_code=diagnosis,
                                          diagnosis_datetime=diagnosis_datetime)
                    yield condition
                except TypeError:
                    logger.info("Parsed string is not a valid ICD-10 code. Skipping...")
                    return
        except WrongXMLFormatError:
            return

    def __validate_xml_diagnosis_path(self, errors: list, file_name: str) -> str | None:
        """Validate that the diagnosis path exists in the parsing map."""
        diagnosis_path = self._sample_parsing_map.get("icd-10_code")
        if diagnosis_path is None:
            errors.append(f"File {file_name} - Condition: No ICD-10 code field found in the XML file. Skipping...")
        return diagnosis_path

    def __validate_xml_patient_id_path(self, errors: list, file_name: str) -> str | None:
        """Validate that the patient ID path exists in the parsing map."""
        patient_id_path = self._sample_parsing_map.get("patient_id")
        if patient_id_path is None:
            errors.append(f"File {file_name} - Condition: No patient ID field found in the XML file. Skipping...")
        return patient_id_path

    def __parse_xml_diagnosis_datetime(self, file_content, validation_errors: list):
        """Parse the optional diagnosis datetime field from XML."""
        diagnosis_datetime_path = self._sample_parsing_map.get("diagnosis_date")
        if diagnosis_datetime_path is None or diagnosis_datetime_path == "":
            return None

        diagnosis_datetime = glom(file_content, diagnosis_datetime_path, default=None)

        if len(diagnosis_datetime) == 0:
            diagnosis_datetime = None
        
        if diagnosis_datetime is not None:
            try:
                diagnosis_datetime = date_parser.parse(diagnosis_datetime[0])
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                validation_errors.append(ParserError("Diagnosis date parsing error"))
        
        return diagnosis_datetime

    def __validate_xml_diagnosis(self, diagnosis: str, patient_id: str, validation_errors: list):
        """Validate that at least one valid diagnosis was found."""
        if not diagnosis:
            validation_errors.append(
                ValueError(f"No correct diagnosis has been found for patient with id {patient_id}")
            )

    def __validate_conditions_from_xml_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            file_content = parse_xml_file(dir_entry)
        except WrongXMLFormatError:
            errors.append(f"File {dir_entry.name} - Wrong XML format [Skipping...]")
            return errors
        
        # Validate mandatory paths
        diagnosis_path = self.__validate_xml_diagnosis_path(errors, dir_entry.name)
        patient_id_path = self.__validate_xml_patient_id_path(errors, dir_entry.name)
        
        if diagnosis_path is None or patient_id_path is None:
            return errors
        
        try:
            condition_index = 0  # Start from 0 for XML elements index
            for diagnosis in glom(file_content, diagnosis_path):
                validation_errors = []
                patient_id = glom(file_content, patient_id_path)
                
                # Parse optional diagnosis datetime
                _ = self.__parse_xml_diagnosis_datetime(file_content, validation_errors)
                
                # Validate diagnosis
                _ = self.__validate_xml_diagnosis(diagnosis, patient_id, validation_errors)

                # If there are validation errors, add them all together
                if validation_errors:
                    for exc in validation_errors:
                        errors.append(f"File {dir_entry.name} - Condition (index {condition_index}): {exc}")
                
                condition_index += 1
                
        except WrongXMLFormatError:
            errors.append(f"File {dir_entry.name} - Wrong XML format [Skipping...]")
            return errors
        return errors