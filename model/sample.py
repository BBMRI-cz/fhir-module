"""Module for Sample representation."""
from datetime import datetime
from typing import List

import simple_icd_10 as icd10
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.extension import Extension
from fhirclient.models.fhirdatetime import FHIRDateTime
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.specimen import Specimen, SpecimenCollection

from model.interface.sample_interface import SampleInterface
from model.storage_temperature import StorageTemperature


class Sample(SampleInterface):
    """Class representing a biological specimen."""

    def __init__(self, identifier: str, donor_id: str, material_type: str = None, diagnoses: list[str] = None,
                 sample_collection_id: str = None,
                 collected_datetime: datetime = None, storage_temperature: StorageTemperature = None) -> None:
        """
        :param identifier: Sample organizational identifier
        :param donor_id: Donor organizational identifier
        :param material_type: Sample type. E.g. tissue, plasma...
        :param diagnosis: ICD-10 classification of the diagnosis
        :param sample_collection_id: Sample collection identifier
        :param collected_datetime: Date and time of sample collection
        :param storage_temperature: Temperature at which the sample is stored
        """
        self._identifier: str = identifier
        self._donor_id: str = donor_id
        self._material_type: str = material_type
        self.diagnoses = []
        if diagnoses is not None:
            for diagnosis in diagnoses:
                if diagnosis is not None and not icd10.is_valid_item(diagnosis):
                    raise TypeError(f"The provided string {diagnosis} is not a valid ICD-10 code.")
            self._diagnoses: list[str] = diagnoses
        self._sample_collection_id: str = sample_collection_id
        self._collected_datetime: datetime = collected_datetime
        self._storage_temperature: StorageTemperature = storage_temperature

    @property
    def identifier(self) -> str:
        """Institutional identifier."""
        return self._identifier

    @property
    def donor_id(self) -> str:
        """Institutional ID of donor."""
        return self._donor_id

    @property
    def material_type(self) -> str:
        """Sample type. E.g. tissue, plasma..."""
        return self._material_type

    @material_type.setter
    def material_type(self, sample_type: str):
        """Sample type. E.g. tissue, plasma..."""
        self._material_type = sample_type

    @property
    def diagnoses(self) -> list[str]:
        """Sample content diagnosis using ICD-10 coding."""
        return self._diagnoses

    @diagnoses.setter
    def diagnoses(self, icd_10_codes: list[str]):
        """Sample content diagnosis using ICD-10 coding."""
        for diagnosis in icd_10_codes:
            if not icd10.is_valid_item(diagnosis):
                raise TypeError(f"The provided string ({diagnosis}) is not a valid ICD-10 code.")
        self._diagnoses = icd_10_codes

    @property
    def sample_collection_id(self) -> str:
        """"Id of collection that this sample is a part of."""""
        return self._sample_collection_id

    @sample_collection_id.setter
    def sample_collection_id(self, sample_collection_id: str):
        self._sample_collection_id = sample_collection_id

    @property
    def collected_datetime(self) -> datetime:
        """Collected datetime. Coding ISO8601"""
        return self._collected_datetime

    @collected_datetime.setter
    def collected_datetime(self, collected_datetime: datetime):
        if not isinstance(collected_datetime,datetime):
            raise TypeError(f"Collected datetime should be type of datetime, but is : {type(collected_datetime)}")
        self._collected_datetime = collected_datetime

    @property
    def storage_temperature(self) -> StorageTemperature:
        """Storage temperature of a sample"""
        return self._storage_temperature

    @storage_temperature.setter
    def storage_temperature(self, storage_temperature: StorageTemperature):
        self._storage_temperature = storage_temperature

    def to_fhir(self, subject_id: str = None, custodian_id: str = None):
        """Return sample representation in FHIR.
        @subject_id: FHIR Resource ID of the sample donor."""
        specimen = Specimen()
        specimen.meta = Meta()
        specimen.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Specimen"]
        specimen.identifier = self.__create_fhir_identifier()
        extensions: List[Extension] = []
        # if material_type_map is not None and self.material_type in material_type_map:
        if self.material_type is not None:
            specimen.type = self.__create_specimen_type()
        if self.collected_datetime is not None:
            specimen.collection = SpecimenCollection()
            specimen.collection.collectedDateTime = FHIRDateTime()

            specimen.collection.collectedDateTime.date = self.collected_datetime.date() if isinstance(
                self.collected_datetime, datetime) else self.collected_datetime
        if subject_id is not None:
            specimen.subject = FHIRReference()
            specimen.subject.reference = f"Patient/{subject_id}"
        if self.diagnoses is not None:
            extensions.extend(self.__create_diagnoses_extension())

        if custodian_id is not None:
            extensions.append(self.__create_custodian_extension(custodian_id))
        if self._storage_temperature is not None:
            extensions.append(self.__create_storage_temperature_extension())
        if extensions:
            specimen.extension = extensions
        return specimen

    def __create_storage_temperature_extension(self) -> Extension:
        storage_temperature_extension: Extension = Extension()
        storage_temperature_extension.url = "https://fhir.bbmri.de/StructureDefinition/StorageTemperature"
        storage_temperature_extension.valueCodeableConcept = CodeableConcept()
        storage_temperature_extension.valueCodeableConcept.coding = [Coding()]
        storage_temperature_extension.valueCodeableConcept.coding[0].code = self.storage_temperature.value
        return storage_temperature_extension

    def __create_diagnoses_extension(self) -> List[Extension]:
        diagnoses_extensions = []
        for diagnosis in self.diagnoses:
            fhir_diagnosis: Extension = Extension()
            fhir_diagnosis.url = "https://fhir.bbmri.de/StructureDefinition/SampleDiagnosis"
            fhir_diagnosis.valueCodeableConcept = CodeableConcept()
            fhir_diagnosis.valueCodeableConcept.coding = [Coding()]
            fhir_diagnosis.valueCodeableConcept.coding[0].code = self.__diagnosis_with_period(diagnosis)
            diagnoses_extensions.append(fhir_diagnosis)
        return diagnoses_extensions

    @staticmethod
    def __create_custodian_extension(custodian_id):
        custodian_extension: Extension = Extension()
        custodian_extension.url = "https://fhir.bbmri.de/StructureDefinition/Custodian"
        custodian_extension.valueReference = FHIRReference()
        custodian_extension.valueReference.reference = f"Organization/{custodian_id}"
        return custodian_extension

    def __create_specimen_type(self) -> CodeableConcept:
        specimen_type = CodeableConcept()
        specimen_type.coding = [Coding()]
        specimen_type.coding[0].code = self.material_type
        specimen_type.coding[0].system = "https://fhir.bbmri.de/CodeSystem/SampleMaterialType"
        return specimen_type

    def __create_fhir_identifier(self):
        """Create fhir identifier."""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]

    @staticmethod
    def __diagnosis_with_period(diagnosis: str) -> str:
        """Returns icd-10 code with a period, e.g., C188 to C18.8"""
        code = diagnosis
        if len(code) == 4 and "." not in code:
            return code[:3] + '.' + code[3:]
        return code

    def __eq__(self, other):
        """Check if two samples are equal.
        @other: Sample to compare with."""
        if not isinstance(other, Sample):
            return False
        return self.identifier == other.identifier and self.donor_id == other.donor_id and \
            self.material_type == other.material_type and self.__compare_diagnoses(other.diagnoses) and \
            self.sample_collection_id == other.sample_collection_id and \
            self.collected_datetime.date() == other.collected_datetime.date() and \
            self.storage_temperature == other.storage_temperature

    def __compare_diagnoses(self, other_diagnoses: list[str]) -> bool:
        """Compare diagnoses, regardless of "." in the ICD-10 code.
        @other_diagnoses: Diagnoses to compare with."""
        current_diagnoses = list(map(self.__diagnosis_with_period, self.diagnoses))
        other_diagnoses = list(map(self.__diagnosis_with_period, other_diagnoses))
        return current_diagnoses == other_diagnoses

    def update_diagnoses(self, new_diagnoses: list[str]):
        """Update sample diagnoses."""
        current_diagnoses = list(map(self.__diagnosis_with_period, self.diagnoses))
        for diagnosis in new_diagnoses:
            if self.__diagnosis_with_period(diagnosis) not in current_diagnoses:
                self.diagnoses.append(diagnosis)

