import abc
from datetime import datetime

from fhirclient.models.bundle import Bundle
from miabis_model import Gender


class SampleDonorInterface:

    @property
    @abc.abstractmethod
    def identifier(self) -> str:
        """return patient identifier"""
        pass

    @identifier.setter
    def identifier(self, identifier: str):
        """set donor identifier"""
        pass

    @property
    @abc.abstractmethod
    def gender(self) -> Gender:
        """get gender"""
        pass

    @gender.setter
    @abc.abstractmethod
    def gender(self, gender: Gender):
        """set gender"""
        pass

    @property
    @abc.abstractmethod
    def date_of_birth(self) -> datetime:
        """get birth_date"""
        pass

    @date_of_birth.setter
    @abc.abstractmethod
    def date_of_birth(self, birth_date: datetime):
        """set birth_date"""
        pass

    @abc.abstractmethod
    def to_fhir(self):
        """get FHIR representation of the resource"""
