import unittest
from typing import List, Callable

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from service.condition_service import ConditionService


class ConditionRepoStub(ConditionRepository):
    conditions = [Condition("C504", "777"), Condition("C505", "777")]

    def get_all(self) -> List[Condition]:
        yield from self.conditions

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".csv", self.__validate_conditions_from_csv_file


class TestConditionService(unittest.TestCase):
    def test_get_all(self):
        condition_service = ConditionService(ConditionRepoStub("XX"))
        self.assertEqual(2, sum(1 for _ in condition_service.get_all()))


if __name__ == '__main__':
    unittest.main()
