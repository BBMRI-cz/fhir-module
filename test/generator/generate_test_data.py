#!/usr/bin/env python3
"""
Test Data Generator Script

This script generates test data files (CSV, JSON, or XML) based on a schema definition.
It creates a new folder with pattern: generated_test_data_{file_type}_{timestamp}

Usage:
    python generate_test_data.py --file-type csv --num-files 5 --records-per-file 100
    python generate_test_data.py --file-type json --num-files 3 --records-per-file 50
    python generate_test_data.py --file-type xml --num-files 10 --records-per-file 1

Note: For XML files, each file contains exactly ONE patient with multiple samples.
"""

import argparse
import json
import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom


class DataGenerator:
    def __init__(self, schema_path: str = "schema.json", generator_dir: Optional[str] = None):
        """Initialize the data generator with schema and reference data."""
        if generator_dir is None:
            generator_dir = Path(__file__).parent
        else:
            generator_dir = Path(generator_dir)
        
        self.generator_dir = generator_dir
        schema_file = generator_dir / schema_path
        
        with open(schema_file, 'r') as f:
            self.schema = json.load(f)
        
        # Load reference data
        self.diagnoses = self._load_json_file("diagnoses.json")
        self.storage_temps = self._load_json_file("storage_temps.json")
        self.material_types = self._load_json_file("material_types.json")
        
        # State tracking for sequential fields
        self.sequential_counters: Dict[str, int] = {}  # Reset per file
        self.sequential_global_counters: Dict[str, int] = {}  # Persist across files
        self.generated_context: Dict[str, Any] = {}
    
    def _load_json_file(self, filename: str) -> List[Any]:
        """Load data from JSON file."""
        filepath = self.generator_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return []
    
    def _get_from_file(self, filename: str) -> Any:
        """Get a random value from a reference file."""
        if filename == "diagnoses.json":
            return random.choice(self.diagnoses) if self.diagnoses else "C000" # NOSONAR
        elif filename == "storage_temps.json":
            return random.choice(self.storage_temps) if self.storage_temps else "temperatureRoom" # NOSONAR
        elif filename == "material_types.json":
            return random.choice(self.material_types) if self.material_types else "blood-serum" # NOSONAR
        return None
    
    def _generate_random_date(self, start_date: str, end_date: str, date_format: str) -> str:
        """Generate a random date between start and end dates."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        time_between = end - start
        days_between = time_between.days
        random_days = random.randrange(days_between) # NOSONAR
        random_date = start + timedelta(days=random_days)
        
        # Add random time if format includes time
        if "%H" in date_format or "%M" in date_format or "%S" in date_format:
            random_date = random_date.replace(
                hour=random.randint(0, 23), # NOSONAR
                minute=random.randint(0, 59), # NOSONAR
                second=random.randint(0, 59) # NOSONAR
            )
        
        return random_date.strftime(date_format)
    
    def _generate_random_year_month(self, start_year: int, end_year: int) -> str:
        """Generate a random year-month in YYYY-MM format."""
        year = random.randint(start_year, end_year) # NOSONAR
        month = random.randint(1, 12) # NOSONAR
        return f"{year}-{month:02d}"
    
    def _generate_random_month(self) -> str:
        """Generate a random month in --MM format."""
        month = random.randint(1, 12) # NOSONAR
        return f"--{month:02d}"
    
    def _handle_sequential(self, field_name: str, field_config: Dict[str, Any]) -> int:
        """Handle sequential field type."""
        if field_name not in self.sequential_counters:
            self.sequential_counters[field_name] = field_config.get("start", 1)
        value = self.sequential_counters[field_name]
        self.sequential_counters[field_name] += 1
        return value
    
    def _handle_sequential_global(self, field_name: str, field_config: Dict[str, Any]) -> int:
        """Handle sequential_global field type."""
        if field_name not in self.sequential_global_counters:
            self.sequential_global_counters[field_name] = field_config.get("start", 1)
        value = self.sequential_global_counters[field_name]
        self.sequential_global_counters[field_name] += 1
        return value
    
    def _handle_random_int(self, field_config: Dict[str, Any]) -> int:
        """Handle random_int field type."""
        return random.randint(field_config["min"], field_config["max"]) # NOSONAR
    
    def _handle_choice(self, field_config: Dict[str, Any]) -> Any:
        """Handle choice field type."""
        return random.choice(field_config["options"]) # NOSONAR
    
    def _handle_from_file(self, field_config: Dict[str, Any]) -> Any:
        """Handle from_file field type."""
        return self._get_from_file(field_config["file"])
    
    def _handle_random_date(self, field_config: Dict[str, Any]) -> str:
        """Handle random_date field type."""
        return self._generate_random_date(
            field_config["start_date"],
            field_config["end_date"],
            field_config.get("format", "%Y-%m-%d")
        )
    
    def _handle_random_datetime(self, field_config: Dict[str, Any]) -> str:
        """Handle random_datetime field type."""
        return self._generate_random_date(
            field_config["start_date"],
            field_config["end_date"],
            field_config.get("format", "%Y-%m-%dT%H:%M:%S")
        )
    
    def _handle_random_year_month(self, field_config: Dict[str, Any]) -> str:
        """Handle random_year_month field type."""
        return self._generate_random_year_month(
            field_config["start_year"],
            field_config["end_year"]
        )
    
    def _handle_random_month(self, field_config: Dict[str, Any]) -> str:
        """Handle random_month field type."""
        return self._generate_random_month()
    
    def _handle_constant(self, field_config: Dict[str, Any]) -> Any:
        """Handle constant field type."""
        return field_config["value"]
    
    def _handle_copy_field(self, field_config: Dict[str, Any]) -> Any:
        """Handle copy_field field type."""
        return self.generated_context.get(field_config["source"])
    
    def _handle_format_string(self, field_config: Dict[str, Any]) -> str:
        """Handle format_string field type."""
        template = field_config["template"]
        return template.format(**self.generated_context)
    
    def _generate_value(self, field_name: str, field_config: Dict[str, Any]) -> Any:
        """Generate a value based on field configuration."""
        field_type = field_config.get("type")
        
        # Handlers that require field_name parameter
        if field_type == "sequential":
            return self._handle_sequential(field_name, field_config)
        elif field_type == "sequential_global":
            return self._handle_sequential_global(field_name, field_config)
        
        # Handlers that only need field_config
        handlers = {
            "random_int": self._handle_random_int,
            "choice": self._handle_choice,
            "from_file": self._handle_from_file,
            "random_date": self._handle_random_date,
            "random_datetime": self._handle_random_datetime,
            "random_year_month": self._handle_random_year_month,
            "random_month": self._handle_random_month,
            "constant": self._handle_constant,
            "copy_field": self._handle_copy_field,
            "format_string": self._handle_format_string,
        }
        
        handler = handlers.get(field_type)
        if handler:
            return handler(field_config)
        
        return None
    
    def generate_csv_record(self) -> Dict[str, Any]:
        """Generate a single CSV record."""
        record = {}
        fields = self.schema.get("csv", {}).get("fields", {})
        
        for field_name, field_config in fields.items():
            record[field_name] = self._generate_value(field_name, field_config)
        
        return record
    
    def generate_json_record(self) -> Dict[str, Any]:
        """Generate a single JSON record."""
        record = {}
        fields = self.schema.get("json", {}).get("fields", {})
        
        for field_name, field_config in fields.items():
            record[field_name] = str(self._generate_value(field_name, field_config))
        
        return record
    
    def generate_xml_patient(self) -> ET.Element:
        """Generate a single XML patient element."""
        xml_config = self.schema.get("xml", {})
        root_element = xml_config.get("root_element", "patient")
        
        # Create root element
        patient = ET.Element(root_element)
        
        # Add root attributes
        root_attrs = xml_config.get("root_attributes", {})
        self.generated_context.clear()
        
        for attr_name, attr_config in root_attrs.items():
            value = self._generate_value(attr_name, attr_config)
            self.generated_context[attr_name] = value
            patient.set(attr_name, str(value))
        
        # Add collections (LTS, STS, etc.)
        collections = xml_config.get("collections", {})
        for collection_name, collection_config in collections.items():
            collection_element = ET.SubElement(patient, collection_name)
            
            # Determine how many sub-elements to create
            count_range = collection_config.get("count_range", [1, 3])
            num_elements = random.randint(count_range[0], count_range[1]) # NOSONAR
            
            element_name = collection_config.get("element", "item")
            
            for _ in range(num_elements):
                # Reset context for each sub-element
                self.generated_context.clear()
                
                sub_element = ET.SubElement(collection_element, element_name)
                
                # Add attributes
                attributes = collection_config.get("attributes", {})
                for attr_name, attr_config in attributes.items():
                    value = self._generate_value(attr_name, attr_config)
                    self.generated_context[attr_name] = value
                    sub_element.set(attr_name, str(value))
                
                # Add fields as child elements
                fields = collection_config.get("fields", {})
                for field_name, field_config in fields.items():
                    value = self._generate_value(field_name, field_config)
                    self.generated_context[field_name] = value
                    field_element = ET.SubElement(sub_element, field_name)
                    field_element.text = str(value)
        
        return patient
    
    def generate_csv_file(self, filepath: Path, num_records: int):
        """Generate a CSV file with specified number of records."""
        fields = self.schema.get("csv", {}).get("fields", {})
        fieldnames = list(fields.keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            
            for _ in range(num_records):
                record = self.generate_csv_record()
                writer.writerow(record)
        
        print(f"Generated CSV file: {filepath}")
    
    def generate_json_file(self, filepath: Path, num_records: int):
        """Generate a JSON file with specified number of records."""
        records = []
        for _ in range(num_records):
            records.append(self.generate_json_record())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
        
        print(f"Generated JSON file: {filepath}")
    
    def generate_xml_file(self, filepath: Path, num_records: int):
        """Generate an XML file with a single patient record.
        
        Note: For XML files, each file contains exactly ONE patient.
        The num_records parameter is ignored for XML to match the expected
        structure where one XML file = one patient with multiple samples.
        """
        # Generate a single patient (the patient generation already includes multiple samples)
        patient = self.generate_xml_patient()
        
        # Pretty print
        xml_str = ET.tostring(patient, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"Generated XML file: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate test data files based on schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file-type csv --num-files 5 --records-per-file 100
  %(prog)s --file-type json --num-files 3 --records-per-file 50
  %(prog)s --file-type xml --num-files 10 --records-per-file 1
  
Note: For XML files, each file contains exactly ONE patient (with multiple samples).
The --records-per-file parameter is ignored for XML files.
        """
    )
    
    parser.add_argument(
        '--file-type',
        type=str,
        choices=['csv', 'json', 'xml'],
        required=True,
        help='Type of files to generate (csv, json, or xml)'
    )
    
    parser.add_argument(
        '--num-files',
        type=int,
        required=True,
        help='Number of files to generate'
    )
    
    parser.add_argument(
        '--records-per-file',
        type=int,
        required=True,
        help='Number of records per file (Note: For XML, this is ignored as each file contains exactly one patient with multiple samples)'
    )
    
    parser.add_argument(
        '--schema',
        type=str,
        default='schema.json',
        help='Path to schema file (default: schema.json)'
    )
    
    args = parser.parse_args()
    
    # Get the generator directory (where this script is located)
    generator_dir = Path(__file__).parent
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = generator_dir / f"generated_test_data_{args.file_type}_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Test Data Generator")
    print(f"{'='*60}")
    print(f"File Type: {args.file_type}")
    print(f"Number of Files: {args.num_files}")
    print(f"Records per File: {args.records_per_file}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*60}\n")
    
    # Initialize generator
    generator = DataGenerator(schema_path=args.schema, generator_dir=str(generator_dir))
    
    # Generate files
    for i in range(1, args.num_files + 1):
        # Reset sequential counters for each file
        # Note: sequential_global_counters are NOT cleared, so they persist across files
        generator.sequential_counters.clear()
        
        if args.file_type == 'csv':
            filepath = output_dir / f"test_data_{i}.csv"
            generator.generate_csv_file(filepath, args.records_per_file)
        
        elif args.file_type == 'json':
            filepath = output_dir / f"test_data_{i}.json"
            generator.generate_json_file(filepath, args.records_per_file)
        
        elif args.file_type == 'xml':
            filepath = output_dir / f"test_data_{i}.xml"
            generator.generate_xml_file(filepath, args.records_per_file)
    
    print(f"\n{'='*60}")
    if args.file_type == 'xml':
        print(f"SUCCESS: Generated {args.num_files} {args.file_type.upper()} file(s)")
        print("         Each file contains 1 patient with multiple samples")
    else:
        print(f"SUCCESS: Generated {args.num_files} {args.file_type.upper()} file(s)")
        print(f"         with {args.records_per_file} records each")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

