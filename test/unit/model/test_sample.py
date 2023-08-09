import unittest

from model.sample import Sample


class TestSample(unittest.TestCase):

    def test_sample_init_empty_args_ok(self):
        self.assertIsInstance(Sample("", ""), Sample)

    def test_sample_to_fhir_ok(self):
        self.assertEqual(Sample("fakeId", "").to_fhir().identifier[0].value, "fakeId")
