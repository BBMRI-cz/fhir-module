import abc
from typing import List

from model.sample_donor import SampleDonor


class SampleDonorRepository(abc.ABC):
    @abc.abstractmethod
    def get_all(self) -> List[SampleDonor]:
        pass
