from datetime import datetime

from miabis_model import Sample, StorageTemperature, Condition

from model.interface.sample_interface import SampleInterface


class SampleMiabis(Sample, SampleInterface):

    def __init__(self, identifier: str, donor_id: str,
                 diagnoses_with_observed_datetime: list[tuple[str, datetime | None]], material_type: str = None,
                 sample_collection_id: str = None,
                 collected_datetime: datetime = None, storage_temperature: StorageTemperature = None):
        super().__init__(identifier, donor_identifier=donor_id, material_type=material_type,
                         collected_datetime=collected_datetime, storage_temperature=storage_temperature,
                         diagnoses_with_observed_datetime=diagnoses_with_observed_datetime)
        self.sample_collection_id = sample_collection_id
        self.condition = Condition(patient_identifier=donor_id)

    @property
    def sample_collection_id(self) -> str:
        return self._sample_collection_id

    @sample_collection_id.setter
    def sample_collection_id(self, collection_id: str):
        self._sample_collection_id = collection_id

    @property
    def diagnoses(self) -> list[str]:
        diagnoses = []
        for diagnosis_with_datetime in self.diagnoses_icd10_code_with_observed_datetime:
            diagnoses.append(diagnosis_with_datetime[0])
        return diagnoses

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, condition: Condition):
        self._condition = condition
