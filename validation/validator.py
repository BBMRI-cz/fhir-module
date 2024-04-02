import abc


class Validator(abc.ABC):
    """Class for handling validation of provided files.
     This class validates if the provided file contains the necessary data for correct transformation."""


    @abc.abstractmethod
    def validate(self) -> bool:
        """Validate if the provided parsing map contains all the necessary attributes"""
