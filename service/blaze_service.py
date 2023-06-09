import requests

from service.patient_service import PatientService


class BlazeService:

    def __init__(self, patient_service: PatientService):
        self._patient_service = patient_service

    def upload_all_patients(self):
        bundle = self._patient_service.get_all_patients_in_fhir()
        response = requests.post(url='http://localhost:8080/fhir', json=bundle.as_json())
        return response.status_code
