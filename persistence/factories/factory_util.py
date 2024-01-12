from persistence.factories.csv_repository_factory import CSVRepositoryFactory
from persistence.factories.repository_factory import RepositoryFactory
from persistence.factories.xml_repository_factory import XMLRepositoryFactory
from util.config import RECORDS_FILE_TYPE


def get_repository_factory() -> RepositoryFactory:
    """This function provides corresponding factory for repositories
    based on the ENV variable which specifies records file type"""
    match RECORDS_FILE_TYPE:
        case "csv":
            return CSVRepositoryFactory()
        case "xml":
            return XMLRepositoryFactory()
        case _:
            raise WrongRecordsFileTypeException


class WrongRecordsFileTypeException(Exception):
    """Raised when unsupported format for records file is given"""
    pass