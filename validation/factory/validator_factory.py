import abc

from validation.validator import Validator


class ValidatorFactory(abc.ABC):
    """Abstract class Representing factory for instantiating validator, regardless of provided file(s) type"""

    @abc.abstractmethod
    def create_validator(self) -> Validator:
        pass
