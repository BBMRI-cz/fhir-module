import unittest

from model.sample_collection import SampleCollection


class TestSampleCollection(unittest.TestCase):
    def test_init(self):
        SampleCollection()

    def test_to_fhir(self):
        sample_collection: SampleCollection = SampleCollection(identifier="test:collection:id",
                                                               acronym="TC",
                                                               name="Test collection")
        self.assertEqual("test:collection:id", sample_collection.to_fhir().identifier[0].value)
        self.assertEqual("Test collection", sample_collection.to_fhir().name)
        self.assertEqual("TC", sample_collection.to_fhir().alias)
