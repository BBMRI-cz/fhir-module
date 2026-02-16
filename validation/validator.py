import abc
import logging
import os

from exception.wrong_parsing_map import WrongParsingMapException
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class Validator(abc.ABC):
    """Class for handling validation of provided files.
     This class validates if the provided file contains the necessary data for correct transformation."""

    def __init__(self, parsing_map: dict, records_dir: str):
        """These properties represent all the necessary values that should be present in parsing map"""
        self._dir_path = records_dir

        self._map_donor = parsing_map.get("donor_map")
        self._donor_id = None
        self._donor_gender = None
        self._donor_birthDate = None

        self._map_sample = parsing_map.get("sample_map")
        self._sample_id = None
        self._sample_material_type = None
        self._sample_diagnosis = None

        self._map_condition = parsing_map.get("condition_map")
        self._condition_icd10 = None
        self._condition_patient_id = None

    @abc.abstractmethod
    def validate(self) -> bool:
        """Validate if the provided parsing map and files for transformation contain all the needed attributes."""
        pass

    @abc.abstractmethod
    def _validate_files_present(self, file_type: str) -> bool:
        """Validates the presence of the files and their type (RECORDS_FILE_TYPE env var) in the
        directory (DIR_PATH env var)."""
        pass

    @abc.abstractmethod
    def _validate_single_file(self, file: os.DirEntry) -> bool:
        """Validates the presence of the necessary attributes (which names are provided by parsing map) in the file."""
        pass

    def _validate_files_structure(self, file_type: str) -> bool:
        """this method validates the files provided by DIR_PATH env variable"""
        self._validate_files_present(file_type)
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith("." + file_type):
                self._validate_single_file(dir_entry)
        logger.info("All the files contain the necessary data/attributes for data transformation.")
        return True

    def _validate_donor_map(self) -> bool:
        """Validates the presence of the donor_map, and all its necessary attributes"""
        if self._map_donor is None:
            logger.error("Provided parsing map does not contain key \"donor_map\"")
            raise WrongParsingMapException

        self._donor_id = self._map_donor.get("id")
        self._donor_gender = self._map_donor.get("gender")
        self._donor_birthDate = self._map_donor.get("birthDate")

        if self._donor_id is None or self._donor_gender is None or self._donor_birthDate is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for donor_map. "
                         f"donor_map needs to contain the following names(attributes): "
                         f" \"id\" \"gender\" \"birthDate\".")
            raise WrongParsingMapException
        logger.info("donor_map and all its name/value pairs are provided.")
        return True

    def _validate_sample_map(self) -> bool:
        """Validates the presence of the sample_map, and all its necessary attributes"""
        if self._map_sample is None:
            logger.error("Provided parsing map does not contain key \"sample_map\"")
            raise WrongParsingMapException

        if self._map_sample.get("sample_details") is None:
            logger.error("Provided parsing map does not contain needed name/value pair of \"sample_details\".")
            raise WrongParsingMapException

        self._sample_id = self._map_sample["sample_details"].get("id")
        self._sample_diagnosis = self._map_sample["sample_details"].get("diagnosis")
        self._sample_material_type = self._map_sample["sample_details"].get("material_type")

        if self._sample_id is None or self._sample_diagnosis is None or self._sample_material_type is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for sample map. "
                         f"sample_map needs to contain the following names(attributes): "
                         f" \"id\", \"diagnosis\", \"material_type\" ")
            raise WrongParsingMapException
        logger.info("sample_map and all its name/value pairs are provided.")
        return True

    def _validate_condition_map(self) -> bool:
        """Validates the presence of the condition_map, and all its necessary attributes"""
        if self._map_condition is None:
            logger.error("Provided parsing map does not contain key \"condition_map\"")
            raise WrongParsingMapException

        self._condition_icd10 = self._map_condition.get("icd-10_code")
        self._condition_patient_id = self._map_condition.get("patient_id")

        if self._condition_icd10 is None or self._condition_patient_id is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for the condition map. "
                         f"condition_map needs to contain the following names(attributes): "
                         f" \"icd-10_code\", \"patient_id\"")
            raise WrongParsingMapException
        logger.info("condition_map and all its name/value pairs are provided.")
        return True

