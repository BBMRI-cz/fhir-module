from typing import List

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    def get_all(self) -> List[SampleDonor]:
        pass