"""Module for handling sample donor persistence"""
import abc
from typing import List

from model.interface.sample_donor_interface import SampleDonorInterface


class SampleDonorRepository(abc.ABC):
    """Class for handling a repository of Sample donors"""

    @abc.abstractmethod
    def get_all(self) -> List[SampleDonorInterface]:
        """Fetches all SampleDonors in repository"""
