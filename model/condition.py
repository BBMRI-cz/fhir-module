"""Module for representing a patient's condition."""
import fhirclient.models.codeableconcept
import fhirclient.models.coding
import fhirclient.models.condition as fhir_condition
import fhirclient.models.fhirreference
import fhirclient.models.meta
import icd10


class Condition:
    """Class representing a patient's medical condition using ICD-10 coding."""

    def __init__(self, icd_10_code: str, patient_id: str):
        if not icd10.exists(icd_10_code):
            raise TypeError("The provided string is not a valid ICD-10 code.")
        self._icd_10_code = icd_10_code
        self._patient_id = patient_id

    @property
    def icd_10_code(self) -> str:
        """Get ICD-10 code with period"""
        return self.__icd_10_code_with_period()

    @property
    def patient_id(self) -> str:
        """Get donor identifier"""
        return self._patient_id

    def to_fhir(self, subject_id: str) -> fhir_condition.Condition:
        """Return condition's representation as a FHIR resource."""
        condition = fhir_condition.Condition()
        condition.meta = fhirclient.models.meta.Meta()
        condition.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Condition"]
        condition.code = fhirclient.models.codeableconcept.CodeableConcept()
        condition.code.coding = [fhirclient.models.coding.Coding()]
        condition.code.coding[0].code = self.__icd_10_code_with_period()
        condition.code.coding[0].system = "http://hl7.org/fhir/sid/icd-10"
        condition.subject = fhirclient.models.fhirreference.FHIRReference()
        condition.subject.reference = "Patient/" + subject_id
        return condition

    def __icd_10_code_with_period(self) -> str:
        """Returns icd-10 code with a period, e.g. C188 to C18.8"""
        code = self._icd_10_code
        if len(code) == 4 and "." not in code:
            return code[:3] + '.' + code[3:]
        return code
