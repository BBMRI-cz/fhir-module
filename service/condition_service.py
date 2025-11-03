from typing import Generator

from model.condition import Condition
from persistence.condition_repository import ConditionRepository


class ConditionService:
    def __init__(self, condition_repository: ConditionRepository):
        self._condition_repository = condition_repository

    def get_all(self) -> Generator[Condition, None, None]:
        for condition in self._condition_repository.get_all():
            yield condition

    def smoke_validate(self, validate_all: bool = False) -> list[str]:
        old_dir_path = self._condition_repository._dir_path
        old_condition_parsing_map = getattr(self._condition_repository, '_condition_parsing_map', None)
        old_separator = getattr(self._condition_repository, '_separator', None)
        
        try:
            self._condition_repository.update_mappings()
            
            result = self._condition_repository.smoke_validate(validate_all)
            
            return result
        finally:
            self._condition_repository._dir_path = old_dir_path
            if old_condition_parsing_map is not None:
                self._condition_repository._condition_parsing_map = old_condition_parsing_map
            if old_separator is not None:
                self._condition_repository._separator = old_separator

    def update_mappings(self) -> None:
        self._condition_repository.update_mappings()