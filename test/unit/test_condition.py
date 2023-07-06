import unittest

from model.condition import Condition


class TestCondition(unittest.TestCase):

    def test_initialize_condition(self):
        condition = Condition("C18.8", "patient-ID")
        self.assertIsInstance(condition, Condition)

