from datetime import datetime

from miabis_model import Sample, StorageTemperature, Observation, DiagnosisReport, Condition
import fhirclient.models.observation as fhir_observation

from model.interface.sample_interface import SampleInterface


class SampleMiabis(Sample, SampleInterface):

    def __init__(self, identifier: str, donor_id: str, material_type: str = None, diagnoses: list[str] = None,
                 sample_collection_id: str = None,
                 collected_datetime: datetime = None, storage_temperature: StorageTemperature = None,
                 diagnosis_observed_datetime: datetime = None):
        super().__init__(identifier, donor_identifier=donor_id, material_type=material_type,
                         collected_datetime=collected_datetime, storage_temperature=storage_temperature)
        self.diagnosis_observed_datetime = diagnosis_observed_datetime
        self.sample_collection_id = sample_collection_id
        if diagnoses is None:
            self.diagnoses = []
            self._observations = []
        else:
            observations = []
            self.diagnoses = diagnoses
            for diagnosis in self.diagnoses:
                observations.append(Observation(diagnosis, sample_identifier=identifier, patient_identifier=donor_id,
                                                diagnosis_observed_datetime=diagnosis_observed_datetime))
            self._observations = observations
        self._diagnosis_report = DiagnosisReport(sample_identifier=identifier, patient_identifier=donor_id)
        self._condition = Condition(patient_identifier=donor_id)

    @property
    def diagnoses(self) -> list[str]:
        return self._diagnoses

    @diagnoses.setter
    def diagnoses(self, diagnoses: list[str]):
        self._diagnoses = diagnoses

    @property
    def sample_collection_id(self) -> str:
        return self._sample_collection_id

    @sample_collection_id.setter
    def sample_collection_id(self, collection_id: str):
        self._sample_collection_id = collection_id

    @property
    def diagnosis_observed_datetime(self):
        return self._diagnosis_observed_datetime

    @diagnosis_observed_datetime.setter
    def diagnosis_observed_datetime(self, observed_datetime: datetime):
        self._diagnosis_observed_datetime = observed_datetime

    @property
    def observations(self) -> list[Observation]:
        return self._observations

    @property
    def diagnosis_report(self) -> DiagnosisReport:
        return self._diagnosis_report

    @property
    def condition(self) -> Condition:
        return self._condition
