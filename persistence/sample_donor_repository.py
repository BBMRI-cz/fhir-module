"""Module for handling sample donor persistence"""
import abc
from typing import List

from model.sample_donor import SampleDonor


class SampleDonorRepository(abc.ABC):
    """Class for handling a repository of Sample donors"""

    @abc.abstractmethod
    def get_all(self) -> List[SampleDonor]:
        """Fetches all SampleDonors in repository"""
