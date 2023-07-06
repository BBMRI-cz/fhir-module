import unittest

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
