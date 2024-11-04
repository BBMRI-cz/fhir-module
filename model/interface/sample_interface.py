import abc
import datetime

from miabis_model import StorageTemperature


class SampleInterface:

    @property
    @abc.abstractmethod
    def identifier(self) -> str:
        """get identifier"""
        pass

    @identifier.setter
    @abc.abstractmethod
    def identifier(self, identifier: str):
        """set identifier"""
        pass

    @property
    @abc.abstractmethod
    def material_type(self) -> str:
        """get material type"""
        pass

    @material_type.setter
    @abc.abstractmethod
    def material_type(self, material_type: str):
        """set material_type"""
        pass

    @property
    @abc.abstractmethod
    def diagnoses(self) -> list[str]:
        """get diagnoses"""
        pass

    @diagnoses.setter
    @abc.abstractmethod
    def diagnoses(self, diagnoses: list[str]):
        """set diagnoses"""
        pass

    @property
    @abc.abstractmethod
    def sample_collection_id(self) -> str:
        """get sample collection id"""
        pass

    @sample_collection_id.setter
    @abc.abstractmethod
    def sample_collection_id(self, collection_id: str):
        """set sample collection id"""
        pass

    @property
    @abc.abstractmethod
    def collected_datetime(self) -> datetime.datetime:
        """get collected datetime"""
        pass

    @collected_datetime.setter
    @abc.abstractmethod
    def collected_datetime(self, collected_datetime: datetime.datetime):
        """set collected datetime"""
        pass

    @property
    @abc.abstractmethod
    def storage_temperature(self):
        """get storage_temperature"""
        pass

    @storage_temperature.setter
    @abc.abstractmethod
    def storage_temperature(self, storage_temperature: StorageTemperature):
        """set storage temperature"""
        pass

    # @property
    # @abc.abstractmethod
    # def diagnosis_observed_datetime(self):
    #     """get datetime when was diagnosis first observed"""
    #     pass
    #
    # @diagnosis_observed_datetime.setter
    # @abc.abstractmethod
    # def diagnosis_observed_datetime(self, observed_datetime: datetime.datetime):
    #     """set datetime when was diagnosis first observed"""
    #     pass

    @abc.abstractmethod
    def to_fhir(self):
        """get FHIR representation of the resource"""
