"""Module for Sample representation."""
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.specimen import Specimen


class Sample:
    """Class representing a biological specimen."""

    def __init__(self, identifier: str, donor_id: str) -> None:
        self._identifier: str = identifier
        self._donor_id: str = donor_id
        self._material_type: str = None

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

    def to_fhir(self):
        """Return sample representation in FHIR."""
        specimen = Specimen()
        specimen.meta = Meta()
        specimen.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Specimen"]
        specimen.identifier = self.__create_fhir_identifier()
        return specimen

    def __create_fhir_identifier(self):
        """Create fhir identifier."""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]
