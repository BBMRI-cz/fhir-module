from fhirclient.models.diagnosticreport import DiagnosticReport
from fhirclient.models.fhirreference import FHIRReference


class MFDiagnosisReport:
    """Class representing a diagnosis report in order to link a specimen to a Condition through this diagnosis report.
    as defined by the MIABIS on FHIR profile.
    @sample_identifier: The identifier of the sample."""
    def __init__(self, sample_identifier: str):
        self._sample_identifier = sample_identifier

    @property
    def sample_id(self) -> str:
        return self._sample_identifier

    def to_fhir(self, sample_id: str):
        diagnosis_report = DiagnosticReport()
        diagnosis_report.specimen = FHIRReference()
        diagnosis_report.specimen.reference = f"Specimen/{sample_id}"
        return diagnosis_report
