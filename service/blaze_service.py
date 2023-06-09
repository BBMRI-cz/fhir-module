import requests

from service.patient_service import PatientService


class BlazeService:

    def __init__(self, patient_service: PatientService):
        self._patient_service = patient_service

    """This method posts all patients from the repository to the Blaze store. WARNING: can result in duplication of
    patients. This method should be called only once, specifically if there are no patients in the FHIR server."""
    def upload_all_patients(self):
        bundle = self._patient_service.get_all_patients_in_fhir_transaction()
        response = requests.post(url='http://localhost:8080/fhir', json=bundle.as_json())
        return response.status_code
