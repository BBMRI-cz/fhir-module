from fhirclient.models.bundle import Bundle

from persistence.sample_donor_repository import SampleDonorRepository


class PatientService:
    def __init__(self, sample_donor_repo: SampleDonorRepository):
        self._sample_donor_repository = sample_donor_repo

    def get_all_patients_in_fhir(self) -> Bundle:
        bundle = Bundle()
        self._sample_donor_repository.get_all()
        return bundle
