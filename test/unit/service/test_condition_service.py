import unittest
from typing import List

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from service.condition_service import ConditionService


class ConditionRepoStub(ConditionRepository):
    conditions = [Condition("C504", "777"), Condition("C505", "777")]

    def get_all(self) -> List[Condition]:
        yield from self.conditions


class TestConditionService(unittest.TestCase):
    def test_get_all(self):
        condition_service = ConditionService(ConditionRepoStub())
        self.assertEqual(2, sum(1 for _ in condition_service.get_all()))


if __name__ == '__main__':
    unittest.main()
