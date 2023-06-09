import uuid

from fhirclient.models.identifier import Identifier
from fhirclient.models.patient import Patient


class SampleDonor:
    def __init__(self, identifier: str):
        if not isinstance(identifier, str):
            raise TypeError("Identifier must be string")
        self._identifier = identifier

    @property
    def identifier(self) -> str:
        return self._identifier

    def to_fhir(self) -> Patient:
        fhir_patient = Patient()
        fhir_patient.identifier = self.__create_fhir_identifier()
        return fhir_patient

    def __create_fhir_identifier(self):
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return fhir_identifier