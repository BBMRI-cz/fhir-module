import uuid
from typing import Generator

from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhirclient.models.resource import Resource

from model.interface.sample_donor_interface import SampleDonorInterface
from persistence.sample_donor_repository import SampleDonorRepository


class PatientService:
    def __init__(self, sample_donor_repo: SampleDonorRepository):
        self._sample_donor_repository = sample_donor_repo

    def get_all_patients_in_fhir_transaction(self) -> Bundle:
        """Fetches all patients/sample donors from the repository as a FHIR bundle."""
        bundle = self.__build_bundle()
        for i, sample_donor in enumerate(self._sample_donor_repository.get_all()):
            patient = sample_donor.to_fhir()
            bundle.entry.append(self.__build_bundle_entry_for_post(patient))
        return bundle

    def get_all(self) -> Generator[SampleDonorInterface, None, None]:
        """Fetches all patients/sample donors from the repository."""
        for donor in self._sample_donor_repository.get_all():
            yield donor

    def __build_bundle(self) -> Bundle:
        bundle = Bundle()
        bundle.type = "transaction"
        bundle.id = str(uuid.uuid4())
        bundle.entry = []
        return bundle

    def __build_bundle_entry_for_post(self, resource: Resource) -> BundleEntry:
        entry = BundleEntry()
        entry.resource = resource
        entry.request = BundleEntryRequest()
        entry.request.method = 'POST'
        entry.request.url = "Patient"
        return entry
