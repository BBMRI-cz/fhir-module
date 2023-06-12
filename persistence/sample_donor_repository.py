import abc
from typing import List

from model.sample_donor import SampleDonor


class SampleDonorRepository(abc.ABC):

    """Fetches all SampleDonors in repository"""
    @abc.abstractmethod
    def get_all(self) -> List[SampleDonor]:
        pass
