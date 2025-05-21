import datetime
import unittest
from typing import cast

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.miabis.sample_miabis import SampleMiabis
from model.sample import Sample
from model.storage_temperature import StorageTemperature
from persistence.sample_xml_repository import SampleXMLRepository
from util.config import PARSING_MAP, STORAGE_TEMP_MAP


class TestSampleXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<materialType>S</materialType>' \
             '<diagnosis>C509</diagnosis>' \
             '<diagnosis_date>2007-10-16</diagnosis_date>' \
             '<storage_temperature>temperatureGN</storage_temperature>' \
             '<cutTime>2021-01-01T00:00:00</cutTime>' \
             '</diagnosisMaterial>' \
             '</STS>'

    sample_no_storage_temperature = \
        '<STS>' \
        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
        '<materialType>S</materialType>' \
        '<diagnosis>C509</diagnosis>' \
        '<cutTime>2021-01-01T00:00:00</cutTime>' \
        '</diagnosisMaterial>' \
        '</STS>'

    sample_no_diagnosis = \
        '<STS>' \
        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
        '<materialType>S</materialType>' \
        '<storage_temperature>temperatureGN</storage_temperature>' \
        '<cutTime>2021-01-01T00:00:00</cutTime>' \
        '</diagnosisMaterial>' \
        '</STS>'

    sample_multiple_diagnoses = \
        '<STS>' \
        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
        '<materialType>S</materialType>' \
        '<diagnosis>C509</diagnosis>' \
        '<diagnosis>C508</diagnosis>' \
        '<storage_temperature>temperatureGN</storage_temperature>' \
        '<cutTime>2021-01-01T00:00:00</cutTime>' \
        '</diagnosisMaterial>' \
        '</STS>'

    sample_no_material_type = \
        '<STS>' \
        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
        '<diagnosis>C509</diagnosis>' \
        '<storage_temperature>temperatureGN</storage_temperature>' \
        '<cutTime>2021-01-01T00:00:00</cutTime>' \
        '</diagnosisMaterial>' \
        '</STS>'

    sample_no_collection_date = \
        '<STS>' \
        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
        '<materialType>S</materialType>' \
        '<diagnosis>C509</diagnosis>' \
        '<storage_temperature>temperatureGN</storage_temperature>' \
        '</diagnosisMaterial>' \
        '</STS>'

    wrong_diagnosis = '<STS>' \
                      '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                      '<diagnosis>wrong</diagnosis>' \
                      '</diagnosisMaterial>' \
                      '</STS>'

    samples = '<STS>' \
              '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
              '<materialType>S</materialType>' \
              '<diagnosis>C508</diagnosis>' \
              '</diagnosisMaterial>' \
              '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136043" year="2032">' \
              '<materialType>T</materialType>' \
              '<diagnosis>C501</diagnosis>' \
              '</diagnosisMaterial>' \
              '</STS>'

    both_collections = '<STS>' \
                       '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                       '<materialType>S</materialType>' \
                       '<diagnosis>C508</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136043" year="2032">' \
                       '<materialType>T</materialType>' \
                       '<diagnosis>C501</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '</STS>' \
                       '<LTS>' \
                       '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136045" year="2032">' \
                       '<materialType>S</materialType>' \
                       '<diagnosis>C508</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136045" year="2032">' \
                       '<materialType>T</materialType>' \
                       '<diagnosis>C501</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '</LTS>'

    wrong_format_content = "This is a wrong format for an xml file."

    content = '<patient id="9999">{sample}</patient>'

    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     material_type_map={"S": "Urine"})
        yield  # run test

    @patchfs
    def test_get_all_one_sample_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        self.assertEqual(1, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertEqual("&:2032:136043", sample.identifier)

    @patchfs
    def test_get_all_two_samples_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        self.assertEqual(2, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, Sample)
            self.assertEqual("&:2032:136043", sample.identifier)

    @patchfs
    def test_with_wrong_parsing_map(self, fake_fs):
        wrong_map = {
            "id": ".",
            "donor_id": "wrong_string"
        }
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path, sample_parsing_map=wrong_map)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))
        wrong_map = {}
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path, sample_parsing_map=wrong_map)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_wrong_file_format_throws_no_error(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.wrong_format_content)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_four_samples_from_two_collections_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.both_collections))
        self.assertEqual(4, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_with_wrong_diagnosis_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.wrong_diagnosis))
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_four_samples_not_none_diagnosis(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.both_collections))
        self.assertEqual(4, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertTrue(len(sample.diagnoses) > 0)

    @patchfs
    def test_with_type_to_collection_map_ok(self, fake_fs):
        spm = PARSING_MAP['sample_map']
        spm['sample_details']['collection'] = "materialType"
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     type_to_collection_map={"S": "test:collection:id"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        for sample in self.sample_repository.get_all():
            self.assertEqual("test:collection:id", sample.sample_collection_id)

    @patchfs
    def test_with_wrong_type_to_collection_map_id_is_none(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     type_to_collection_map={"not_present": "test:collection:id"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        self.assertEqual(None, next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_multiple_diagnosis_ok(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'])
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_multiple_diagnoses))
        for sample in self.sample_repository.get_all():
            self.assertEqual(2, len(sample.diagnoses))
            self.assertEqual("C50.9", sample.diagnoses[0])
            self.assertEqual("C50.8", sample.diagnoses[1])

    @patchfs
    def test_multiple_diagnosis_to_fhir_ok(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'])
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_multiple_diagnoses))
        for sample in self.sample_repository.get_all():
            self.assertEqual(2, len(sample.diagnoses))
            self.assertEqual("C50.9", sample.to_fhir().extension[0].valueCodeableConcept.coding[0].code)
            self.assertEqual("C50.8", sample.to_fhir().extension[1].valueCodeableConcept.coding[0].code)

    @patchfs
    def test_storage_temperature_ok(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        self.assertEqual(StorageTemperature.TEMPERATURE_GN, next(self.sample_repository.get_all()).storage_temperature)

    @patchfs
    def test_storage_temperature_code_not_in_map(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map={"bad": "code"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        self.assertIsNone(next(self.sample_repository.get_all()).storage_temperature)

    @patchfs
    def test_storage_temperature_not_in_sample(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP,
                                                     material_type_map={"S": "Urine"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_no_storage_temperature))
        for sample in self.sample_repository.get_all():
            self.assertIsNone(sample.storage_temperature)
            self.assertEqual("Urine", sample.material_type)
            self.assertEqual("C50.9", sample.diagnoses[0])
            self.assertEqual(datetime.datetime(2021, 1, 1, 0, 0), sample.collected_datetime)

    @patchfs
    def test_diagnosis_not_in_sample(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_no_diagnosis))
        for sample in self.sample_repository.get_all():
            self.assertEqual(StorageTemperature.TEMPERATURE_GN, sample.storage_temperature)
            self.assertEqual("Urine", sample.material_type)
            self.assertEqual(len(sample.diagnoses), 0)
            self.assertEqual(datetime.datetime(2021, 1, 1, 0, 0), sample.collected_datetime)

    @patchfs
    def test_material_type_not_in_sample(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_no_material_type))
        for sample in self.sample_repository.get_all():
            self.assertEqual(StorageTemperature.TEMPERATURE_GN, sample.storage_temperature)
            self.assertIsNone(sample.material_type)
            self.assertEqual("C50.9", sample.diagnoses[0])
            self.assertEqual(datetime.datetime(2021, 1, 1, 0, 0), sample.collected_datetime)

    @patchfs
    def test_no_collection_date(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP,
                                                     material_type_map={"S": "Urine"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample_no_collection_date))
        for sample in self.sample_repository.get_all():
            self.assertIsNone(sample.collected_datetime)
            self.assertEqual(StorageTemperature.TEMPERATURE_GN, sample.storage_temperature)
            self.assertEqual("Urine", sample.material_type)
            self.assertEqual("C50.9", sample.diagnoses[0])

    @patchfs
    def test_collection_with_correct_attribute_to_collection(self, fake_fs):
        spm = PARSING_MAP['sample_map']
        spm['sample_details']['collection'] = "diagnosis"
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     type_to_collection_map={"C509": "test:collection:id"})
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        for sample in self.sample_repository.get_all():
            self.assertEqual("test:collection:id", sample.sample_collection_id)

    @patchfs
    def test_diagnosis_date_miabis_model(self, fake_fs):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'],
                                                     storage_temp_map=STORAGE_TEMP_MAP,
                                                     material_type_map={"S": "Urine"},
                                                     miabis_on_fhir_model=True)

        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, SampleMiabis)
            sample = cast(SampleMiabis, sample)
            observations = sample.observations
            self.assertEqual(observations[0].diagnosis_observed_datetime,
                             datetime.datetime(year=2007, month=10, day=16))
