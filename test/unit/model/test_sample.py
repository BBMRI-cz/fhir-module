import datetime
import unittest

from model.sample import Sample
from model.storage_temperature import StorageTemperature


class TestSample(unittest.TestCase):

    def test_sample_init_empty_args_ok(self):
        self.assertIsInstance(Sample("", ""), Sample)

    def test_sample_to_fhir_ok(self):
        self.assertEqual(Sample("fakeId", "").to_fhir().identifier[0].value, "fakeId")

    def test_assign_sample_type_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", material_type="tissue")
        self.assertEqual("tissue", sample.material_type)

    def test_material_type_to_fhir_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", material_type="dna")
        self.assertEqual("dna", sample.to_fhir(material_type_map={"dna": "dna"}).type.coding[0].code)

    def test_material_type_not_in_map_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", material_type="dna")
        self.assertIsNone(sample.to_fhir(material_type_map={"something": "not"}).type)

    def test_material_type_is_none_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertIsNone(sample.to_fhir(material_type_map={"something": "not"}).type)
        self.assertIsNone(sample.to_fhir(material_type_map={}).type)
        self.assertIsNone(sample.to_fhir().type)

    def test_to_fhir_subject_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertEqual("Patient/PatientFHIRId", sample.to_fhir(subject_id="PatientFHIRId").subject.reference)

    def test_get_icd_10_diagnosis_none(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertIsNone(sample.diagnosis)

    def test_set_correct_icd_10_diagnosis_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", diagnosis="C50.1")
        self.assertEqual("C50.1", sample.diagnosis)

    def test_diagnosis_without_dot_is_added_to_fhir(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", diagnosis="C501")
        self.assertTrue(sample.to_fhir().extension)
        self.assertEqual("C50.1", sample.to_fhir().extension[0].valueCodeableConcept.coding[0].code)

    def test_to_fhir_no_extensions_if_no_special_attributes(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertFalse(sample.to_fhir().extension)

    def test_to_fhir_sample_custodian_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertEqual("Organization/FHIRCollectionID", sample.to_fhir(custodian_id="FHIRCollectionID")
                         .extension[0].valueReference.reference)

    def test_sample_collection_id_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient", sample_collection_id="test")
        self.assertEqual("test", sample.sample_collection_id)

    def test_storage_temp_is_none(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient")
        self.assertIsNone(sample.storage_temperature)

    def test_storage_temp_is_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient",
                                storage_temperature=StorageTemperature.TEMPERATURE_GN)
        self.assertEqual(StorageTemperature.TEMPERATURE_GN, sample.storage_temperature)

    def test_assign_storage_temp(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient",
                                storage_temperature=StorageTemperature.TEMPERATURE_GN)
        self.assertEqual(StorageTemperature.TEMPERATURE_GN, sample.storage_temperature)
        sample.storage_temperature = StorageTemperature.TEMPERATURE_2_TO_10
        self.assertEqual(StorageTemperature.TEMPERATURE_2_TO_10, sample.storage_temperature)

    def test_to_fhir_storage_temperature_ok(self):
        sample: Sample = Sample(identifier="sampleId", donor_id="patient",
                                storage_temperature=StorageTemperature.TEMPERATURE_GN)
        self.assertEqual("temperatureGN", sample.to_fhir().extension[0].valueCodeableConcept.coding[0].code)

    def test_collected_datetime_ok(self):
        collected_datetime = datetime.datetime(year=2025,month=3,day=18)
        sample: Sample = Sample(identifier="sampleID", donor_id="donor", collected_datetime=collected_datetime)
        self.assertEqual("2025-03-18T00:00:00", sample.collected_datetime.isoformat())
        self.assertEqual("2025-03-18T00:00:00", sample.to_fhir().collection.collectedDateTime.isoformat())

    def test_collected_datetime_from_string_no_day_ok(self):
        collected_datetime = datetime.datetime.strptime("2022-03", '%Y-%m')
        sample: Sample = Sample(identifier="sampleID", donor_id="donor", collected_datetime=collected_datetime)
        self.assertEqual("2022-03-01T00:00:00", sample.collected_datetime.isoformat())
        self.assertEqual("2022-03-01T00:00:00", sample.to_fhir().collection.collectedDateTime.isoformat())

    def test_collected_datetime_from_string_year_only_ok(self):
        collected_datetime = datetime.datetime.strptime("2022", '%Y')
        sample: Sample = Sample(identifier="sampleID", donor_id="donor", collected_datetime=collected_datetime)
        self.assertEqual("2022-01-01T00:00:00", sample.collected_datetime.isoformat())
        self.assertEqual("2022-01-01T00:00:00", sample.to_fhir().collection.collectedDateTime.isoformat())