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
from util.config import get_records_dir_path, get_parsing_map, get_sample_collections_path, get_type_to_collection_map, \
    get_storage_temp_map, get_material_type_map, get_biobank_path, get_miabis_material_type_map, \
    get_miabis_storage_temp_map


class JsonRepositoryFactory(RepositoryFactory):
    """This class instantiates repositories that work with csv files"""

    def create_condition_repository(self, miabis_on_fhir_model: bool = False) -> ConditionRepository:
        return ConditionJsonRepository(records_path=get_records_dir_path(),
                                      condition_parsing_map=get_parsing_map()['condition_map'])

    def create_sample_collection_repository(self, miabis_on_fhir_model: bool = False) -> SampleCollectionRepository:
        return SampleCollectionJSONRepository(get_sample_collections_path(), miabis_on_fhir_model)

    def create_sample_repository(self, miabis_on_fhir_model: bool = False) -> SampleRepository:
        if miabis_on_fhir_model:
            material_type_map = get_miabis_material_type_map()
            storage_temp_map = get_miabis_storage_temp_map()
        else:
            material_type_map = get_material_type_map()
            storage_temp_map = get_storage_temp_map()
        return SampleJsonRepository(records_path=get_records_dir_path(),
                                   sample_parsing_map=get_parsing_map()['sample_map'],
                                   type_to_collection_map=get_type_to_collection_map(),
                                   storage_temp_map=storage_temp_map,
                                   material_type_map=material_type_map,
                                   miabis_on_fhir_model=miabis_on_fhir_model)

    def create_sample_donor_repository(self, miabis_on_fhir_model: bool = False) -> SampleDonorRepository:
        return SampleDonorJsonRepository(records_path=get_records_dir_path(),
                                        donor_parsing_map=get_parsing_map()['donor_map'],
                                        miabis_on_fhir_model=miabis_on_fhir_model)

    def create_biobank_repository(self) -> BiobankRepository:
        return BiobankJSONRepository(biobank_json_file_path=get_biobank_path())
