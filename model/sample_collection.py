"""Module for handling SampleCollection operations"""
from fhirclient.models.identifier import Identifier
from fhirclient.models.organization import Organization


class SampleCollection:
    """Sample Collection represents a set of samples with at least one common characteristic."""

    def __init__(self, identifier: str = None, name: str = None, acronym: str = None):
        """
        :param identifier: Collection identifier same format as in the BBMRI-ERIC directory.
        :param name: Name of the collection.
        :param acronym: Acronym of the collection.
        """
        self._identifier: str = identifier
        self._name: str = name
        self._acronym: str = acronym

    def to_fhir(self) -> Organization:
        fhir_organization = Organization()
        fhir_organization.identifier = self.__create_fhir_identifier()
        if self._name is not None:
            fhir_organization.name = self._name
        if self._acronym is not None:
            fhir_organization.alias = self._acronym
        return fhir_organization

    def __create_fhir_identifier(self):
        """Create fhir identifier."""
        fhir_identifier = Identifier()
        fhir_identifier.value = self._identifier
        return [fhir_identifier]
