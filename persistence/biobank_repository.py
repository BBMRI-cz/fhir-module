import abc

from miabis_model import Biobank


class BiobankRepository:
    @abc.abstractmethod
    def get_biobank(self) -> Biobank:
        """Get Biobank"""
        pass
