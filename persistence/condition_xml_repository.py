"""Module containing classes tied to condition persistence in XML files"""
from typing import List

from model.condition import Condition
from persistence.condition_repository import ConditionRepository


class ConditionXMLRepository(ConditionRepository):
    """Class for handling condition persistence in XML files"""
    def get_all(self) -> List[Condition]:
        pass