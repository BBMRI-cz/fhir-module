from enum import Enum


class Gender(Enum):
    MALE = 1
    FEMALE = 2
    OTHER = 3
    UNKNOWN = 4

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


