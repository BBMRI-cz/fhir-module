import unittest

from model.sample import Sample


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
