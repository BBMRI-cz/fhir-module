#!/bin/bash -e

# Update shared_config.json with values for JSON test configuration
CONFIG_FILE=${1:-"util/shared_config.json"}

echo "Updating $CONFIG_FILE for JSON test configuration..."

# Update all configuration values for JSON tests
jq '.RECORDS_DIR_PATH = "/opt/records" |
    .PARSING_MAP_PATH = "/opt/mappings/json_parsing_map.json" |
    .MIABIS_MATERIAL_TYPE_MAP_PATH = "/opt/mappings/miabis_material_type_map.json" |
    .RECORDS_FILE_TYPE = "json"' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"

jq '.RECORDS_DIR_PATH = "/opt/records" |
    .PARSING_MAP_PATH = "/opt/mappings/json_parsing_map.json" |
    .MATERIAL_TYPE_MAP_PATH = "/opt/fhir-module/util/default_material_type_map.json" |
    .MIABIS_MATERIAL_TYPE_MAP_PATH = "/opt/mappings/miabis_material_type_map.json" |
    .SAMPLE_COLLECTIONS_PATH = "/opt/fhir-module/util/default_sample_collection.json" |
    .TYPE_TO_COLLECTION_MAP_PATH = "/opt/mappings/type_to_collection_map.json" |
    .STORAGE_TEMP_MAP_PATH = "/opt/fhir-module/util/default_storage_temp_map.json" |
    .MIABIS_STORAGE_TEMP_MAP_PATH = "/opt/fhir-module/util/default_miabis_storage_temp_map.json" |
    .RECORDS_FILE_TYPE = "json"' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"

echo "Updated configuration:"
echo "  - RECORDS_DIR_PATH: /opt/records"
echo "  - PARSING_MAP_PATH: /opt/mappings/json_parsing_map.json"
echo "  - MATERIAL_TYPE_MAP_PATH: /opt/fhir-module/util/default_material_type_map.json"
echo "  - MIABIS_MATERIAL_TYPE_MAP_PATH: /opt/mappings/miabis_material_type_map.json"
echo "  - SAMPLE_COLLECTIONS_PATH: /opt/fhir-module/util/default_sample_collection.json"
echo "  - TYPE_TO_COLLECTION_MAP_PATH: /opt/mappings/type_to_collection_map.json"
echo "  - STORAGE_TEMP_MAP_PATH: /opt/fhir-module/util/default_storage_temp_map.json"
echo "  - MIABIS_STORAGE_TEMP_MAP_PATH: /opt/fhir-module/util/default_miabis_storage_temp_map.json"
echo "  - RECORDS_FILE_TYPE: json"
echo "Configuration updated successfully!"

