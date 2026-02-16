from persistence.biobank_json_repository import BiobankJSONRepository
from persistence.biobank_repository import BiobankRepository
from persistence.condition_json_repository import ConditionJsonRepository
from persistence.condition_repository import ConditionRepository
from persistence.factories.repository_factory import RepositoryFactory
from persistence.sample_collection_json_repository import SampleCollectionJSONRepository
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.sample_donor_json_repository import SampleDonorJsonRepository
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.sample_json_repository import SampleJsonRepository
from persistence.sample_repository import SampleRepository
from util.config import RECORDS_DIR_PATH, PARSING_MAP, SAMPLE_COLLECTIONS_PATH, TYPE_TO_COLLECTION_MAP, \
    STORAGE_TEMP_MAP, MATERIAL_TYPE_MAP, BIOBANK_PATH, MIABIS_MATERIAL_TYPE_MAP, \
    MIABIS_STORAGE_TEMP_MAP


class JsonRepositoryFactory(RepositoryFactory):
    """This class instantiates repositories that work with csv files"""

    def create_condition_repository(self, miabis_on_fhir_model: bool = False) -> ConditionRepository:
        return ConditionJsonRepository(records_path=RECORDS_DIR_PATH,
                                      condition_parsing_map=PARSING_MAP['condition_map'])

    def create_sample_collection_repository(self, miabis_on_fhir_model: bool = False) -> SampleCollectionRepository:
        return SampleCollectionJSONRepository(SAMPLE_COLLECTIONS_PATH, miabis_on_fhir_model)

    def create_sample_repository(self, miabis_on_fhir_model: bool = False) -> SampleRepository:
        if miabis_on_fhir_model:
            material_type_map = MIABIS_MATERIAL_TYPE_MAP
            storage_temp_map = MIABIS_STORAGE_TEMP_MAP
        else:
            material_type_map = MATERIAL_TYPE_MAP
            storage_temp_map = STORAGE_TEMP_MAP
        return SampleJsonRepository(records_path=RECORDS_DIR_PATH,
                                   sample_parsing_map=PARSING_MAP['sample_map'],
                                   type_to_collection_map=TYPE_TO_COLLECTION_MAP,
                                   storage_temp_map=storage_temp_map,
                                   material_type_map=material_type_map,
                                   miabis_on_fhir_model=miabis_on_fhir_model)

    def create_sample_donor_repository(self, miabis_on_fhir_model: bool = False) -> SampleDonorRepository:
        return SampleDonorJsonRepository(records_path=RECORDS_DIR_PATH,
                                        donor_parsing_map=PARSING_MAP['donor_map'],
                                        miabis_on_fhir_model=miabis_on_fhir_model)

    def create_biobank_repository(self) -> BiobankRepository:
        return BiobankJSONRepository(biobank_json_file_path=BIOBANK_PATH)
