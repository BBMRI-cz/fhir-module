"""Module for Sample representation."""
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.specimen import Specimen


class Sample:
    """Class representing a biological specimen."""

    def __init__(self, identifier: str, donor_id: str, material_type: str = None) -> None:
        self._identifier: str = identifier
        self._donor_id: str = donor_id
        self._material_type: str = material_type

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

    def to_fhir(self, material_type_map: dict = None):
        """Return sample representation in FHIR."""
        specimen = Specimen()
        specimen.meta = Meta()
        specimen.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Specimen"]
        specimen.identifier = self.__create_fhir_identifier()
        if material_type_map is not None and self.material_type in material_type_map:
            specimen.type = self.__create_specimen_type(material_type_map)
        return specimen

    def __create_specimen_type(self, material_type_map) -> CodeableConcept:
        specimen_type = CodeableConcept()
        specimen_type.coding = [Coding()]
        specimen_type.coding[0].code = material_type_map.get(self.material_type)
        specimen_type.coding[0].system = "https://fhir.bbmri.de/CodeSystem/SampleMaterialType"
        return specimen_type

    def __create_fhir_identifier(self):
        """Create fhir identifier."""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]
