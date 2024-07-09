from persistence.condition_csv_repository import ConditionCsvRepository
from persistence.condition_repository import ConditionRepository
from persistence.factories.repository_factory import RepositoryFactory
from persistence.sample_collection_json_repository import SampleCollectionJSONRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.sample_csv_repository import SampleCsvRepository
from persistence.sample_donor_csv_repository import SampleDonorCsvRepository
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.sample_repository import SampleRepository
from util.config import RECORDS_DIR_PATH, CSV_SEPARATOR, PARSING_MAP, SAMPLE_COLLECTIONS_PATH, TYPE_TO_COLLECTION_MAP,STORAGE_TEMP_MAP,COLLECTION_MAPPING_ATTRIBUTE


class CSVRepositoryFactory(RepositoryFactory):
    """This class instantiates repositories that work with csv files"""
    def create_condition_repository(self) -> ConditionRepository:
        return ConditionCsvRepository(records_path=RECORDS_DIR_PATH,
                                      separator=CSV_SEPARATOR,
                                      condition_parsing_map=PARSING_MAP['condition_map'])

    def create_sample_collection_repository(self) -> SampleCollectionRepository:
        return SampleCollectionJSONRepository(SAMPLE_COLLECTIONS_PATH)

    def create_sample_repository(self) -> SampleRepository:
        return SampleCsvRepository(records_path=RECORDS_DIR_PATH,
                                   sample_parsing_map=PARSING_MAP['sample_map'],
                                   separator=CSV_SEPARATOR,
                                   type_to_collection_map=TYPE_TO_COLLECTION_MAP,
                                   storage_temp_map=STORAGE_TEMP_MAP)

    def create_sample_donor_repository(self) -> SampleDonorRepository:
        return SampleDonorCsvRepository(records_path=RECORDS_DIR_PATH,
                                        separator=CSV_SEPARATOR,
                                        donor_parsing_map=PARSING_MAP['donor_map'])
