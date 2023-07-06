"""Module for representing a patient's condition."""
import icd10


class Condition:
    """Class representing a patient's medical condition using ICD-10 coding."""
    def __init__(self, icd_10_code: str, patient_id: str):
        if not icd10.exists(icd_10_code):
            raise TypeError("The provided string is not a valid ICD-10 code.")
        self.icd_10_code = icd_10_code
        self.patient_id = patient_id
