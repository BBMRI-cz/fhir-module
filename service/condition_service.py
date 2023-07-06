from typing import Generator

from persistence.condition_repository import ConditionRepository


class ConditionService:
    def __init__(self, condition_repository: ConditionRepository):
        self._condition_repository = condition_repository

    def get_all(self) -> Generator:
        for condition in self._condition_repository.get_all():
            yield condition
