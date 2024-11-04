"""Sample donor module"""
from _datetime import datetime

from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.patient import Patient

from model.gender import Gender
from model.interface.sample_donor_interface import SampleDonorInterface


class SampleDonor(SampleDonorInterface):
    """Class representing a sample donor/patient"""

    def __init__(self, identifier: str, gender: Gender = None, birth_date: datetime = None):
        if not isinstance(identifier, str):
            raise TypeError("Identifier must be string")
        self._identifier = identifier
        self._gender: Gender = gender
        self._date_of_birth: datetime = birth_date

    @property
    def identifier(self) -> str:
        """Institutional identifier"""
        return self._identifier

    @property
    def gender(self) -> Gender:
        """Administrative gender"""
        return self._gender

    @property
    def date_of_birth(self) -> datetime:
        """Date of birth"""
        if self._date_of_birth is not None:
            return self._date_of_birth
        else:
            return None

    @gender.setter
    def gender(self, gender: Gender):
        """Ser administrative gender"""
        if not isinstance(gender, Gender):
            raise TypeError("Gender must be from a list of values: " + str(Gender.list()))
        self._gender = gender

    @date_of_birth.setter
    def date_of_birth(self, date: datetime):
        """Date of birth. Coding ISO8601"""
        if not isinstance(date, datetime):
            raise TypeError("Date of birth must be a date.")
        self._date_of_birth = date

    def to_fhir(self) -> Patient:
        """Return sample donor representation in FHIR"""
        fhir_patient = Patient()
        fhir_patient.meta = Meta()
        fhir_patient.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Patient"]
        fhir_patient.identifier = self.__create_fhir_identifier()
        if self.gender is not None:
            fhir_patient.gender = self._gender.name.lower()
        if self.date_of_birth is not None:
            fhir_patient.birthDate = FHIRDate()
            fhir_patient.birthDate.date = self.date_of_birth.date()
        return fhir_patient

    def __create_fhir_identifier(self):
        """Create fhir identifier"""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]
