import uuid
from enum import Enum

from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.patient import Patient

from model.gender import Gender


class SampleDonor:
    def __init__(self, identifier: str):
        if not isinstance(identifier, str):
            raise TypeError("Identifier must be string")
        self._identifier = identifier
        self._gender: Gender = None

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def gender(self) -> Gender:
        return self._gender

    @gender.setter
    def gender(self, gender: Gender):
        self._gender = gender

    def to_fhir(self) -> Patient:
        fhir_patient = Patient()
        fhir_patient.meta = Meta()
        fhir_patient.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Patient"]
        fhir_patient.identifier = self.__create_fhir_identifier()
        return fhir_patient

    def __create_fhir_identifier(self):
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]




