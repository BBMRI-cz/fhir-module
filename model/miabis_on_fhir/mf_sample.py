import logging
from datetime import datetime

from fhirclient.models.annotation import Annotation
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.extension import Extension
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.identifier import Identifier
from fhirclient.models.meta import Meta
from fhirclient.models.specimen import Specimen, SpecimenCollection

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()

class MFSample:
    """Class representing a biological specimen as defined by the MIABIS on FHIR profile."""
    def __init__(self, identifier: str, donor_id: str, material_type: str = None, collected_datetime: str = None,
                 body_site: str = None, body_site_system: str = None, storage_temperature: str = None, use_restrictions: str = None):
        """
        :param identifier: Sample organizational identifier
        :param donor_id: Donor organizational identifier
        :param material_type: Sample type. E.g. tissue, plasma...
        :param collected_datetime: Date and time of sample collection
        :param body_site: The anatomical location from which the sample was collected
        :param body_site_system: The system to which the body site belongs
        :param storage_temperature: Temperature at which the sample is stored
        :param use_restrictions: Restrictions on the use of the sample
        """
        self._identifier = identifier
        self._donor_id = donor_id
        self._material_type = material_type
        self._collected_datetime = collected_datetime
        self._body_site = body_site
        self._body_site_system = body_site_system
        self._storage_temperature = storage_temperature
        self._use_restrictions = use_restrictions

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
    def material_type(self, material_type: str):
        self._material_type = material_type

    @property
    def collected_datetime(self) -> str:
        """Date and time of sample collection."""
        return self._collected_datetime

    @collected_datetime.setter
    def collected_datetime(self, collected_datetime: str):
        self._collected_datetime = datetime.strptime(collected_datetime, '%Y-%m-%dT%H:%M:%S')
        self._collected_datetime = collected_datetime

    @property
    def body_site(self) -> str:
        """The anatomical location from which the sample was collected."""
        return self._body_site

    @body_site.setter
    def body_site(self, body_site: str):
        self._body_site = body_site

    @property
    def body_site_system(self) -> str:
        """The system to which the body site belongs."""
        return self._body_site_system

    @body_site_system.setter
    def body_site_system(self, body_site_system: str):
        self._body_site_system = body_site_system

    @property
    def storage_temperature(self) -> str:
        """Temperature at which the sample is stored."""
        return self._storage_temperature

    @storage_temperature.setter
    def storage_temperature(self, storage_temperature: str):
        self._storage_temperature = storage_temperature

    @property
    def use_restrictions(self) -> str:
        """Restrictions on the use of the sample."""
        return self._use_restrictions

    @use_restrictions.setter
    def use_restrictions(self, use_restrictions: str):
        self._use_restrictions = use_restrictions

    # TODO  provide map of storage temperatures ?
    def to_fhir(self, material_type_map: dict = None, subject_id: str = None):
        """return sample representation in FHIR format
        :param material_type_map: Mapping of material types to FHIR codes
        :param subject_id: FHIR ID of the subject to which the sample belongs"""

        specimen = Specimen()
        specimen.meta = Meta()
        # TODO add url for the structure definition
        specimen.meta.profile = ["https://example.org/StructureDefinition/Specimen"]
        specimen.identifier = self.__create_fhir_identifier()
        extensions: list[Extension] = []
        if material_type_map is not None and self.material_type in material_type_map:
            specimen.type = self.__create_specimen_type(material_type_map)
        elif self.material_type is not None and self.material_type not in material_type_map:
            logger.error(f"Material type {self.material_type} not found in material type map")
        if self.collected_datetime is not None or self.body_site is not None:
            specimen.collection = SpecimenCollection()
            if self.collected_datetime is not None:
                specimen.collection.collectedDateTime = self.collected_datetime
            if self.body_site is not None:
                specimen.collection.bodySite = self.__create_body_site()
            if subject_id is not None:
                specimen.subject = FHIRReference()
                specimen.subject.reference = f"Patient/{subject_id}"
            if self.storage_temperature is not None:
                extensions.append(self.__create_storage_temperature_extension())
            if self.use_restrictions is not None:
                specimen.note = [Annotation()]
                specimen.note[0].text = self.use_restrictions
            return specimen

    def __create_fhir_identifier(self):
        """Create fhir identifier."""
        fhir_identifier = Identifier()
        fhir_identifier.value = self.identifier
        return [fhir_identifier]

    def __create_specimen_type(self, material_type_map) -> CodeableConcept:
        """Create specimen type codeable concept."""
        specimen_type = CodeableConcept()
        specimen_type.coding = [Coding()]
        specimen_type.coding[0].code = material_type_map.get(self.material_type)
        specimen_type.coding[0].system = "http://example.org/ValueSet/miabis-material-type-VS"
        return specimen_type

    def __create_body_site(self) -> CodeableConcept:
        """Create body site codeable concept."""
        body_site = CodeableConcept()
        body_site.coding = [Coding()]
        body_site.coding[0].code = self.body_site
        if self.body_site_system is not None:
            body_site.coding[0].system = self.body_site_system
        return body_site
    
    def __create_storage_temperature_extension(self):
        """Create storage temperature extension."""
        # TODO SUBJECT TO CHANGE: storage temperature should be taken from json file ? same as material type
        storage_temperature_extension: Extension = Extension()
        storage_temperature_extension.url = "https://example.org/StructureDefinition/StorageTemperature"
        storage_temperature_extension.valueCodeableConcept = CodeableConcept()
        storage_temperature_extension.valueCodeableConcept.coding = [Coding()]
        storage_temperature_extension.valueCodeableConcept.coding[0].code = self.storage_temperature
        return storage_temperature_extension
