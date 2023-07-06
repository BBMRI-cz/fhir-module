"""Module for representing a patient's condition"""


class Condition:
    """Class representing a patient's medical condition"""
    def __init__(self, icd_10_code: str, patient_id: str):
        self.icd_10_code = icd_10_code
        self.patient_id = patient_id
