"""This module contains a class for patient's gender"""
from enum import Enum


class Gender(Enum):
    """Enum for expressing patient's gender"""
    MALE = 1
    FEMALE = 2
    OTHER = 3
    UNKNOWN = 4

    @classmethod
    def list(cls):
        """List all possible gender values"""
        return list(map(lambda c: c.value, cls))
