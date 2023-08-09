import unittest

import fhirclient.models.condition

from model.condition import Condition


class TestCondition(unittest.TestCase):

    def test_initialize_condition(self):
        condition = Condition("C18.8", "patient-ID")
        self.assertIsInstance(condition, Condition)

    def test_wrong_icd_10_code_throws_error(self):
        with self.assertRaises(TypeError):
            Condition("C7777", "patient-ID")
        with self.assertRaises(TypeError):
            Condition("77", "patient-ID")
        with self.assertRaises(TypeError):
            Condition("rand_string", "patient-ID")

    def test_get_icd_10_code(self):
        condition = Condition("C18.8", "patient-ID")
        self.assertEqual("C18.8", condition.icd_10_code)
        condition = Condition("C188", "patient-ID")
        self.assertEqual("C18.8", condition.icd_10_code)

    def test_to_fhir(self):
        condition = Condition("C18.8", "patient-ID")
        self.assertIsInstance(condition.to_fhir("fake_fhir_id"), fhirclient.models.condition.Condition)

    def test_to_fhir_valid_icd_10_code(self):
        condition = Condition("C18.8", "patient-ID")
        self.assertEqual("C18.8", condition.to_fhir("fake_fhir_id").code.coding[0].code)

    def test_to_fhir_period_is_added_to_icd_10_code(self):
        condition = Condition("C188", "patient-ID")
        self.assertEqual("C18.8", condition.to_fhir("fake_fhir_id").code.coding[0].code)
        condition = Condition("A18", "patient-ID")
        self.assertEqual("A18", condition.to_fhir("fake_fhir_id").code.coding[0].code)
