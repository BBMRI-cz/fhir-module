"""Module for handling sample donor persistence"""
import abc
from typing import List, Generator

from model.interface.sample_donor_interface import SampleDonorInterface


class SampleDonorRepository(abc.ABC):
    """Class for handling a repository of Sample donors"""

    @abc.abstractmethod
    def get_all(self) -> Generator[SampleDonorInterface,None,None]:
        """Fetches all SampleDonors in repository"""
