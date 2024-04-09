import abc
import logging

from exception.wrong_parsing_map import WrongParsingMapException

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class Validator(abc.ABC):
    """Class for handling validation of provided files.
     This class validates if the provided file contains the necessary data for correct transformation."""

    @abc.abstractmethod
    def validate(self) -> bool:
        """Validate if the provided parsing map contains all the necessary attributes"""

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

    def _maps_are_present(self) -> bool:
        if self._map_condition is None:
            logger.error("Provided parsing map does not contain key \"condition_map\"")
            raise WrongParsingMapException
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
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for donor_map."
                         f"donor_map needs to contain the following names(attributes): \"id\" \"gender\" \"birthDate\".")
            raise WrongParsingMapException
        return True

    def _validate_sample_map(self) -> bool:
        """Validates the presence of the sample_map, and all its necessary attributes"""
        # TODO Subject to change - in csv, the sample map does not need nested sample_details dictionary, it can be removed
        if self._map_sample is None:
            logger.error("Provided parsing map does not contain key \"sample_map\"")
            raise WrongParsingMapException
        # TODO OBJECT TO CHANGE
        if self._map_sample.get("sample_details") is None:
            logger.error("Provided parsing map does not contain needed name/value pair of \"sample_details\".")
            raise WrongParsingMapException

        self._sample_id = self._map_sample["sample_details"].get("id")
        self._sample_diagnosis = self._map_sample["sample_details"].get("diagnosis")
        self._sample_material_type = self._map_sample["sample_details"].get("material_type")

        if self._sample_id is None or self._sample_diagnosis is None or self._sample_material_type is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for sample map."
                         f"sample_map needs to contain the following names(attributes):"
                         f" \"id\", \"diagnosis\", \"material_type\" ")
            raise WrongParsingMapException
        return True

    def _validate_condition_map(self) -> bool:
        """Validates the presence of the condition_map, and all its necessary attributes"""
        if self._map_condition is None:
            logger.error("Provided parsing map does not contain key \"condition_map\"")
            raise WrongParsingMapException

        self._condition_icd10 = self._map_condition.get("icd-10_code")
        self._condition_patient_id = self._map_condition.get("patient_id")

        if self._condition_icd10 is None or self._condition_patient_id is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for the condition map."
                         f"condition_map needs to contain the following names(attributes):"
                         f" \"icd-10_code\", \"patient_id\"")
            raise WrongParsingMapException
        return True

    def _get_properties(self) -> list[str]:
        return [attr for attr in dir(self) if attr.startswith(("_donor", "_sample", "condition"))]
