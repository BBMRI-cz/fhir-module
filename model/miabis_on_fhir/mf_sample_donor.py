from datetime import datetime

from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.extension import Extension
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.patient import Patient

from model.gender import Gender


class MFSampleDonor:
    """Class representing a sample donor/patient as defined by the MIABIS on FHIR profile."""
    def __init__(self, identifier: str, gender: Gender = None, birth_date: datetime = None, datasetType: str = None):
        """
        :param identifier: Sample donor identifier
        :param gender: Gender of the donor
        :param birth_date: Date of birth of the donor
        :param datasetType: Dataset that the donor belongs to
        """
        if not isinstance(identifier, str):
            raise TypeError("Identifier must be string")
        self._identifier = identifier
        self._gender = gender
        self._date_of_birth = birth_date
        self._datasetType = datasetType

    @property
    def identifier(self) -> str:
        """Institutional identifier"""
        return self._identifier

    @property
    def gender(self) -> Gender:
        return self._gender

    @gender.setter
    def gender(self, gender: Gender):
        if not isinstance(gender,Gender):
            raise TypeError("Gender must be from a list of values: " + str(Gender.list()))
        self._gender = gender

    @property
    def date_of_birth(self) -> datetime | None:
        if self._date_of_birth is not None:
            return self._date_of_birth
        else:
            return None

    @property
    def datasetType(self) -> str:
        return self._datasetType

    def to_fhir(self) -> Patient:
        """Return sample donor representation in FHIR"""
        fhir_patient = Patient()
        fhir_patient.meta = Meta()
        fhir_patient.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Patient"]
        fhir_patient.identifier = self.__create_fhir_identifier()
        extensions: list[Extension] = []
        if self.gender is not None:
            fhir_patient.gender = self._gender.name.lower()
        if self.date_of_birth is not None:
            fhir_patient.birthDate = FHIRDate()
            fhir_patient.birthDate.date = self.date_of_birth.date()
        if self.datasetType is not None:
            extensions.append(self.__create_dataset_extension())
        if extensions:
            fhir_patient.extension = extensions
        return fhir_patient

    def __create_fhir_identifier(self):
        """Create fhir identifier"""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]

    def __create_dataset_extension(self):
        fhir_dataset: Extension = Extension()
        fhir_dataset.url = "https://example.org/StructureDefinition/datasetType"
        fhir_dataset.valueCodeableConcept = CodeableConcept()
        fhir_dataset.valueCodeableConcept.coding = [Coding()]
        fhir_dataset.valueCodeableConcept.coding[0].code = self.datasetType
        return fhir_dataset
