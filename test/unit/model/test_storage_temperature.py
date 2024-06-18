import unittest

from model.storage_temperature import StorageTemperature
from util.enums_util import parse_storage_temp_from_code


class TestStorageTemperature(unittest.TestCase):

    def test_storage_temperature_parse_from_code_correct_codes(self):
        storage_temp_map = {
            "temperature2to10": "TEMPERATURE_2_TO_10",
            "temperature-18to-35": "TEMPERATURE_MINUS_18_TO_MINUS_35",
            "temperature-60to-85": "TEMPERATURE_MINUS_60_TO_MINUS_85",
            "temperatureGN": "TEMPERATURE_GN",
            "temperatureLN": "TEMPERATURE_LN",
            "temperatureRoom": "TEMPERATURE_ROOM",
            "temperatureOther": "TEMPERATURE_OTHER"
        }
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperature2to10"), StorageTemperature.TEMPERATURE_2_TO_10)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperature-18to-35"),
                         StorageTemperature.TEMPERATURE_MINUS_18_TO_MINUS_35)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperature-60to-85"),
                         StorageTemperature.TEMPERATURE_MINUS_60_TO_MINUS_85)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperatureGN"), StorageTemperature.TEMPERATURE_GN)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperatureLN"), StorageTemperature.TEMPERATURE_LN)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperatureRoom"), StorageTemperature.TEMPERATURE_ROOM)
        self.assertEqual(parse_storage_temp_from_code(storage_temp_map, "temperatureOther"), StorageTemperature.TEMPERATURE_OTHER)

    def test_storage_temperature_parse_from_code_incorrect_code_returns_None(self):
        storage_temp_map = {
            "temperature2to10": "TEMPERATURE_2_TO_10",
        }
        self.assertIsNone(parse_storage_temp_from_code(storage_temp_map, "badcode"))


    def test_parse_storage_temperature_from_code_matched_value_not_in_enum_returns_None(self):
        storage_temp_map = {
            "temperature2to10": "BAD_VALUE",
        }
        self.assertIsNone(parse_storage_temp_from_code(storage_temp_map, "temperature2to10"))

    def test_parse_storage_temperature_from_none_(self):
        storage_temp_map = {
            "temperature2to10": "BAD_VALUE",
        }
        self.assertIsNone(parse_storage_temp_from_code(storage_temp_map,None))