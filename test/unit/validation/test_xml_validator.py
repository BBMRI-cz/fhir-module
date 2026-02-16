import unittest
from pyfakefs.fake_filesystem_unittest import patchfs

from exception.no_files_provided import NoFilesProvidedException
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from util.config import PARSING_MAP
from validation.xml_validator import XMLValidator


class TestXMLValidator(unittest.TestCase):
    test_xml = """<?xml version="1.0" encoding="utf-8" ?>
<!--These are completely synthetic dummy_files with the same structure-->
<patient xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" biobank="MOU" consent="true" id="33" month="--01"
         sex="female" xmlns="http://www.bbmri.cz/schemas/biobank/data"
         xsi:noNamespaceSchemaLocation="exportNIS.xsd" year="1999">
    <LTS>
        <tissue number="888" sampleId="BBM:2032:888:1" year="2032">
            <samplesNo>3</samplesNo>
            <availableSamplesNo>3</availableSamplesNo>
            <materialType>1</materialType>
            <pTNM>T4bN1M</pTNM>
            <morphology>8500/32</morphology>
            <diagnosis>C509</diagnosis>
            <cutTime>2032-11-23T09:40:00</cutTime>
            <freezeTime>2032-11-23T09:08:00</freezeTime>
            <retrieved>operational</retrieved>
        </tissue>
        <tissue number="888" sampleId="BBM:2032:888:4" year="2032">
            <samplesNo>3</samplesNo>
            <availableSamplesNo>3</availableSamplesNo>
            <materialType>4</materialType>
            <pTNM>T4bN1M</pTNM>
            <morphology>8500/32</morphology>
            <diagnosis>C61</diagnosis>
            <cutTime>2032-11-23T09:40:00</cutTime>
            <freezeTime>2032-11-23T10:08:00</freezeTime>
            <retrieved>operational</retrieved>
        </tissue>
        <tissue number="888" sampleId="BBM:2032:888:53" year="2032">
            <samplesNo>1</samplesNo>
            <availableSamplesNo>1</availableSamplesNo>
            <materialType>53</materialType>
            <pTNM>T4bN1M</pTNM>
            <morphology>8500/32</morphology>
            <diagnosis>C509</diagnosis>
            <cutTime>2032-11-23T09:40:00</cutTime>
            <freezeTime>2032-11-23T11:08:00</freezeTime>
            <retrieved>operational</retrieved>
        </tissue>
        <tissue number="888" sampleId="BBM:2032:888:54" year="2032">
            <samplesNo>1</samplesNo>
            <availableSamplesNo>1</availableSamplesNo>
            <materialType>54</materialType>
            <pTNM>T4bN1M</pTNM>
            <morphology>8500/32</morphology>
            <diagnosis>C549</diagnosis>
            <cutTime>2032-11-23T09:40:00</cutTime>
            <freezeTime>2032-11-23T11:08:00</freezeTime>
            <retrieved>operational</retrieved>
        </tissue>
    </LTS>
    <STS>
        <diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">
            <materialType>S</materialType>
            <diagnosis>C509</diagnosis>
            <takingDate>2032-10-4T10:02:00</takingDate>
            <retrieved>unknown</retrieved>
        </diagnosisMaterial>
    </STS>
</patient>"""
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
        fake_fs.create_file(self.dir_path + "mock.xml", contents=self.test_xml)
        self.validator = XMLValidator(PARSING_MAP, self.dir_path)
        self.assertTrue(self.validator.validate())

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
