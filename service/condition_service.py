from typing import Generator

from model.condition import Condition
from persistence.condition_repository import ConditionRepository


class ConditionService:
    def __init__(self, condition_repository: ConditionRepository):
        self._condition_repository = condition_repository

    def get_all(self) -> Generator[Condition, None, None]:
        for condition in self._condition_repository.get_all():
            yield condition
