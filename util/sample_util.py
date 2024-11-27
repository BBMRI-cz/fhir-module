import re

from model.sample import Sample
from model.storage_temperature import StorageTemperature
from dateutil import parser as date_parser


def build_sample_from_json(sample_json: dict, donor_identifier: str, collection_identifier: str) -> Sample:
    """
    Builds a Sample object from a JSON representation.
    :param sample_json: JSON representation of a sample
    :param donor_identifier: Donor organizational identifier (given by organization, not by Blaze server)
    :param collection_identifier: Sample collection identifier (given by organization, not by Blaze server)
    """
    material_type = None
    diagnosis = []
    storage_temperature = None
    collected_datetime = None
    identifier = sample_json.get("identifier")[0]["value"]
    if sample_json.get("type") is not None:
        material_type = sample_json.get("type").get("coding")[0].get("code")
    if sample_json.get("collection") is not None:
        collected_datetime = date_parser.parse(sample_json.get("collection").get("collectedDateTime"))
        collected_datetime = collected_datetime.replace(hour=0, minute=0, second=0)
    for ext in sample_json.get("extension", []):
        match ext["url"]:
            case "https://fhir.bbmri.de/StructureDefinition/SampleDiagnosis":
                diagnosis.append(ext["valueCodeableConcept"]["coding"][0]["code"])
            case "https://fhir.bbmri.de/StructureDefinition/StorageTemperature":
                storage_temperature = StorageTemperature(ext["valueCodeableConcept"]["coding"][0]["code"])

    sample = Sample(identifier, donor_identifier, material_type, diagnosis, collection_identifier, collected_datetime,
                    storage_temperature)
    return sample


def diagnosis_with_period(diagnosis: str) -> str:
    """Returns icd-10 code with a period, e.g., C188 to C18.8"""
    code = diagnosis
    if len(code) == 4 and "." not in code:
        return code[:3] + '.' + code[3:]
    return code


def extract_all_diagnosis(diagnosis_str: str) -> list[str]:
    """Extract all diagnosis from a string"""
    parsed_diagnoses = []
    pattern = r'\b[A-Z][0-9]{2}(?:\.)?(?:[0-9]{1,2})?\b'
    diagnoses = re.findall(pattern, diagnosis_str)
    for diagnosis in diagnoses:
        parsed_diagnoses.append(diagnosis_with_period(diagnosis))
    return parsed_diagnoses
