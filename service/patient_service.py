import uuid

from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhirclient.models.meta import Meta

from persistence.sample_donor_repository import SampleDonorRepository


class PatientService:
    def __init__(self, sample_donor_repo: SampleDonorRepository):
        self._sample_donor_repository = sample_donor_repo

    def get_all_patients_in_fhir(self) -> Bundle:
        bundle = Bundle()
        bundle.type = "transaction"
        bundle.id = str(uuid.uuid4())
        bundle.entry = []
        for i, donor in enumerate(self._sample_donor_repository.get_all()):
            entry = BundleEntry()
            donor_fhir = donor.to_fhir()
            donor_fhir.meta = Meta()
            donor_fhir.meta.profile = ["https://fhir.bbmri.de/StructureDefinition/Patient"]
            donor_fhir.id = str(i)
            entry.resource = donor_fhir
            entry.fullUrl = "http://localhost:8080/fhir/Patient/" + donor_fhir.id
            entry.request = BundleEntryRequest()
            entry.request.method = 'PUT'
            entry.request.url = "Patient/" + donor_fhir.id
            print(entry.as_json())
            bundle.entry.append(entry)
        return bundle
