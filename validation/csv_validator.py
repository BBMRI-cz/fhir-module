import logging

from util.custom_logger import setup_logger
from validator import Validator
from util.config import PARSING_MAP
from exception.wrong_parsing_map import WrongParsingMapException
setup_logger()
logger = logging.getLogger()


class CsvValidator(Validator):

    def __init__(self):
        """These properties represent all the necessary values that should be present in parsing map"""
        self._donor_map = PARSING_MAP.get("donor_map")
        self._donor_id = None
        self._donor_gender = None
        self._donor_birthDate = None
        self._sample_map = PARSING_MAP.get("sample_map")
        self._sample_id = None
        self._sample_material_type = None
        self._sample_diagnosis = None
        self._condition_map = PARSING_MAP.get("condition_map")
        self._condition_icd10 = None
        self._condition_patient_id = None

    def _maps_are_present(self) -> bool:
        if self._condition_map is None:
            logger.error("Provided parsing map does not contain key \"condition_map\"")
            raise WrongParsingMapException
        return True

    def _validate_donor_map(self) -> bool :
        if self._donor_map is None:
            logger.error("Provided parsing map does not contain key \"donor_map\"")
            raise WrongParsingMapException

        self._donor_id = self._donor_map["id"]
        self._donor_gender = self._donor_map["gender"]
        self._donor_birthDate = self._donor_map["birthDate"]

        if self._donor_id is None or self._donor_gender is None or self._donor_birthDate is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for donor_map."
                         f"donor_map needs to contain the following names(attributes): \"id\" \"gender\" \"birthDate\".")
            raise WrongParsingMapException
        return True

    def _validate_sample_map(self) -> bool:
        # TODO Subject to change - in csv, the sample map does not need nested sample_details dictionary, it can be removed
        if self._sample_map is None:
            logger.error("Provided parsing map does not contain key \"sample_map\"")
            raise WrongParsingMapException
        # TODO OBJECT TO CHANGE
        if self._sample_map.get("sample_details") is None:
            logger.error("Provided parsing map does not contain needed name/value pair of \"sample_details\".")
            raise WrongParsingMapException

        self._sample_id = self._sample_map["sample_details"]["id"]
        self._sample_diagnosis = self._sample_map["sample_details"]["diagnosis"]
        self._sample_material_type = self._sample_map["sample_details"]["material_type"]

        if self._sample_id is None or self._sample_diagnosis is None or self._sample_material_type is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for sample map."
                         f"sample_map needs to contain the following names(attributes):"
                         f" \"id\", \"diagnosis\", \"material_type\" ")
        return True
    def _validate_condition_map(self) -> bool:
        if self._condition_map is None:
            logger.error("Provided parsing map does not contain key \"condition_map\"")
            raise WrongParsingMapException

        self._condition_icd10 = self._condition_map["icd-10_code"]
        self._condition_patient_id = self._condition_map["patient_id"]

        if self._condition_icd10 is None or self._condition_patient_id is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for the condition map."
                         f"condition_map needs to contain the following names(attributes):"
                         f" \"icd-10_code\", \"patient_id\"")
            return True

    def validate(self) -> bool:
        pass
