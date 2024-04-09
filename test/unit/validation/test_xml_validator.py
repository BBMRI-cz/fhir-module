import unittest
from pyfakefs.fake_filesystem_unittest import patchfs

from exception.no_files_provided import NoFilesProvidedException
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from util.config import PARSING_MAP
from validation.xml_validator import XMLValidator


class TestXMLValidator(unittest.TestCase):
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

    missing_materialType = '<STS>' \
                       '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                       '<diagnosis>C508</diagnosis>' \
                       '<diagnosis>C501</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '</STS>'

    content = '<patient id="9999">{sample}</patient>'

    dir_path = "/mock_dir/"

    missing_donor_parsing_map = {
        "sample_map": {
            "sample": "**.STS.* || **.LTS.*",
            "sample_details": {
                "id": "@sampleId",
                "material_type": "materialType",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient.@id"
        },
        "condition_map": {
            "icd-10_code": "**.diagnosis",
            "patient_id": "patient.@id"
        }
    }

    missing_sample_parsing_map = {
        "donor_map": {
            "id": "patient.@id",
            "gender": "patient.@sex",
            "birthDate": "patient.@year"
        },
        "condition_map": {
            "icd-10_code": "**.diagnosis",
            "patient_id": "patient.@id"
        }
    }

    missing_condition_parsing_map = {
        "donor_map": {
            "id": "patient.@id",
            "gender": "patient.@sex",
            "birthDate": "patient.@year"
        },
        "sample_map": {
            "sample": "**.STS.* || **.LTS.*",
            "sample_details": {
                "id": "@sampleId",
                "material_type": "materialType",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient.@id"
        }
    }

    missing_donor_id_parsing_map = {
        "donor_map": {
            "gender": "patient.@sex",
            "birthDate": "patient.@year"
        },
        "sample_map": {
            "sample": "**.STS.* || **.LTS.*",
            "sample_details": {
                "id": "@sampleId",
                "material_type": "materialType",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient.@id"
        },
        "condition_map": {
            "icd-10_code": "**.diagnosis",
            "patient_id": "patient.@id"
        }
    }

    missing_subsample_parsing_map = {
        "donor_map": {
            "id": "patient.@id",
            "gender": "patient.@sex",
            "birthDate": "patient.@year"
        },
        "sample_map": {
            "sample_details": {
                "id": "@sampleId",
                "material_type": "materialType",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient.@id"
        },
        "condition_map": {
            "icd-10_code": "**.diagnosis",
            "patient_id": "patient.@id"
        }
    }

    missing_condition_patient_id_parsing_map = {
        "donor_map": {
            "id": "patient.@id",
            "gender": "patient.@sex",
            "birthDate": "patient.@year"
        },
        "sample_map": {
            "sample": "**.STS.* || **.LTS.*",
            "sample_details": {
                "id": "@sampleId",
                "material_type": "materialType",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient.@id"
        },
        "condition_map": {
            "icd-10_code": "**.diagnosis"
        }
    }

    @patchfs
    def test_xml_validator_correct_parsing_map_and_file(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(PARSING_MAP, self.dir_path)
        self.assertTrue(self.validator.validate)

    @patchfs
    def test_xml_validator_no_csv_files_present_in_records_directory_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "bad_file_format.txt")
        self.validator = XMLValidator(PARSING_MAP, self.dir_path)
        self.assertRaises(NoFilesProvidedException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_donor_map_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_donor_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_sample_maps_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_sample_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_condition_map_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_condition_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_donor_id_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_donor_id_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_subsample_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_subsample_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_validator_missing_condition_patient_id_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.both_collections))
        self.validator = XMLValidator(self.missing_condition_patient_id_parsing_map, self.dir_path)
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_xml_actual_file_missing_defined_sample_material_field(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.content.format(sample=self.missing_materialType))
        self.validator = XMLValidator(PARSING_MAP, self.dir_path)
        self.assertRaises(NonexistentAttributeParsingMapException, self.validator.validate)
