#!/usr/bin/env python3
"""
Synthea Data Generator for Healthcare Simulation

This module provides functionality to generate realistic synthetic patient data
using Synthea and convert it to HL7 v2.x format for use in healthcare simulations.

The generator creates diverse patient scenarios with realistic clinical data,
demographics, and medical histories that can be used to test healthcare applications.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import yaml
import random
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheaGenerator:
    """Generates realistic synthetic patient data using Synthea."""
    
    def __init__(self, synthea_jar_path: Optional[str] = None, output_dir: str = "synthea_output"):
        """
        Initialize the Synthea generator.
        
        Args:
            synthea_jar_path: Path to Synthea JAR file. If None, will attempt to download.
            output_dir: Directory to store generated data
        """
        self.synthea_jar_path = synthea_jar_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Ensure Synthea JAR is available
        if not self.synthea_jar_path:
            self.synthea_jar_path = self._download_synthea()
        
        if not os.path.exists(self.synthea_jar_path):
            raise FileNotFoundError(f"Synthea JAR not found at {self.synthea_jar_path}")
    
    def _download_synthea(self) -> str:
        """Download Synthea JAR file if not present."""
        synthea_dir = Path("synthea")
        synthea_dir.mkdir(exist_ok=True)
        
        jar_path = synthea_dir / "synthea-with-dependencies.jar"
        
        if jar_path.exists():
            logger.info(f"Using existing Synthea JAR: {jar_path}")
            return str(jar_path)
        
        logger.info("Downloading Synthea JAR...")
        try:
            # Download the latest Synthea JAR
            import urllib.request
            url = "https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar"
            urllib.request.urlretrieve(url, jar_path)
            logger.info(f"Downloaded Synthea JAR to: {jar_path}")
            return str(jar_path)
        except Exception as e:
            logger.error(f"Failed to download Synthea: {e}")
            raise
    
    def generate_patients(self, 
                         num_patients: int = 10,
                         state: str = "Massachusetts",
                         city: str = "Boston",
                         age_min: int = 0,
                         age_max: int = 100,
                         seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate synthetic patients using Synthea.
        
        Args:
            num_patients: Number of patients to generate
            state: US state for patient demographics
            city: City for patient demographics
            age_min: Minimum age for generated patients
            age_max: Maximum age for generated patients
            seed: Random seed for reproducible results
            
        Returns:
            Dictionary containing generation results and metadata
        """
        logger.info(f"Generating {num_patients} patients for {city}, {state}")
        
        # Create temporary directory for this generation run
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Prepare Synthea command
            cmd = [
                "java", "-jar", self.synthea_jar_path,
                "-p", str(num_patients),
                "-s", str(seed) if seed else str(random.randint(1000, 9999)),
                "-a", f"{age_min}-{age_max}",
                "-c", f"Massachusetts/{city}",
                "-o", str(temp_path)
            ]
            
            try:
                # Run Synthea
                logger.info(f"Running Synthea command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.error(f"Synthea generation failed: {result.stderr}")
                    raise RuntimeError(f"Synthea generation failed: {result.stderr}")
                
                # Move generated files to output directory
                generation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                generation_dir = self.output_dir / f"generation_{generation_id}"
                generation_dir.mkdir(exist_ok=True)
                
                # Copy FHIR files
                fhir_dir = generation_dir / "fhir"
                fhir_dir.mkdir(exist_ok=True)
                
                if (temp_path / "fhir").exists():
                    for fhir_file in (temp_path / "fhir").glob("*.json"):
                        shutil.copy2(fhir_file, fhir_dir)
                
                # Copy CSV files if they exist
                csv_dir = generation_dir / "csv"
                csv_dir.mkdir(exist_ok=True)
                
                for csv_file in temp_path.glob("*.csv"):
                    shutil.copy2(csv_file, csv_dir)
                
                # Generate metadata
                metadata = {
                    "generation_id": generation_id,
                    "timestamp": datetime.now().isoformat(),
                    "num_patients": num_patients,
                    "state": state,
                    "city": city,
                    "age_range": f"{age_min}-{age_max}",
                    "seed": seed,
                    "fhir_files": len(list(fhir_dir.glob("*.json"))),
                    "csv_files": len(list(csv_dir.glob("*.csv")))
                }
                
                # Save metadata
                with open(generation_dir / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Generated {metadata['fhir_files']} FHIR files and {metadata['csv_files']} CSV files")
                return metadata
                
            except subprocess.TimeoutExpired:
                logger.error("Synthea generation timed out")
                raise RuntimeError("Synthea generation timed out")
            except Exception as e:
                logger.error(f"Error during Synthea generation: {e}")
                raise
    
    def list_generations(self) -> List[Dict[str, Any]]:
        """List all available generations."""
        generations = []
        
        for gen_dir in self.output_dir.glob("generation_*"):
            metadata_file = gen_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    generations.append(metadata)
        
        return sorted(generations, key=lambda x: x["timestamp"], reverse=True)
    
    def get_fhir_patients(self, generation_id: str) -> List[Dict[str, Any]]:
        """
        Load FHIR patient data from a specific generation.
        
        Args:
            generation_id: ID of the generation to load
            
        Returns:
            List of FHIR Patient resources
        """
        generation_dir = self.output_dir / f"generation_{generation_id}"
        fhir_dir = generation_dir / "fhir"
        
        if not fhir_dir.exists():
            raise FileNotFoundError(f"FHIR directory not found for generation {generation_id}")
        
        patients = []
        for fhir_file in fhir_dir.glob("*.json"):
            try:
                with open(fhir_file, "r") as f:
                    fhir_data = json.load(f)
                    
                    # Synthea generates Bundle resources containing Patient resources
                    if fhir_data.get("resourceType") == "Bundle":
                        for entry in fhir_data.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "Patient":
                                patients.append(resource)
                    elif fhir_data.get("resourceType") == "Patient":
                        patients.append(fhir_data)
                        
            except Exception as e:
                logger.warning(f"Failed to load FHIR file {fhir_file}: {e}")
        
        logger.info(f"Loaded {len(patients)} patients from generation {generation_id}")
        return patients
    
    def get_csv_data(self, generation_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load CSV data from a specific generation.
        
        Args:
            generation_id: ID of the generation to load
            
        Returns:
            Dictionary mapping CSV filenames to their data
        """
        import csv
        
        generation_dir = self.output_dir / f"generation_{generation_id}"
        csv_dir = generation_dir / "csv"
        
        if not csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found for generation {generation_id}")
        
        csv_data = {}
        for csv_file in csv_dir.glob("*.csv"):
            try:
                with open(csv_file, "r") as f:
                    reader = csv.DictReader(f)
                    csv_data[csv_file.stem] = list(reader)
            except Exception as e:
                logger.warning(f"Failed to load CSV file {csv_file}: {e}")
        
        return csv_data


class SyntheaToHL7Converter:
    """Converts Synthea FHIR data to HL7 v2.x messages."""
    
    def __init__(self):
        """Initialize the converter."""
        self.loinc_codes = self._load_loinc_codes()
        self.icd10_codes = self._load_icd10_codes()
    
    def _load_loinc_codes(self) -> Dict[str, str]:
        """Load LOINC codes for observations."""
        # Common LOINC codes for vital signs and lab values
        return {
            "heart_rate": "8867-4",
            "systolic_bp": "8480-6", 
            "diastolic_bp": "8462-4",
            "temperature": "8310-5",
            "respiratory_rate": "9279-1",
            "oxygen_saturation": "2708-6",
            "glucose": "2345-7",
            "hemoglobin": "718-7",
            "hematocrit": "4544-3",
            "creatinine": "2160-0",
            "hemoglobin_a1c": "4548-4"
        }
    
    def _load_icd10_codes(self) -> Dict[str, str]:
        """Load ICD-10 codes for diagnoses."""
        # Common ICD-10 codes
        return {
            "diabetes_type2": "E11.9",
            "hypertension": "I10",
            "chest_pain": "R07.9",
            "stroke": "I63.9",
            "pneumonia": "J18.9",
            "myocardial_infarction": "I21.9"
        }
    
    def convert_patient_to_hl7(self, 
                              fhir_patient: Dict[str, Any],
                              csv_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                              message_type: str = "ADT^A01") -> str:
        """
        Convert a FHIR Patient resource to HL7 v2.x message.
        
        Args:
            fhir_patient: FHIR Patient resource
            csv_data: Optional CSV data for additional clinical information
            message_type: HL7 message type (default: ADT^A01)
            
        Returns:
            HL7 v2.x message string
        """
        # Generate message header
        msh = self._create_msh_segment(message_type)
        
        # Generate patient identification
        pid = self._create_pid_segment(fhir_patient)
        
        # Generate patient visit
        pv1 = self._create_pv1_segment(fhir_patient)
        
        # Generate diagnoses
        dg1_segments = self._create_dg1_segments(fhir_patient, csv_data)
        
        # Generate observations
        obx_segments = self._create_obx_segments(fhir_patient, csv_data)
        
        # Generate procedures
        pr1_segments = self._create_pr1_segments(fhir_patient, csv_data)
        
        # Combine all segments
        segments = [msh, pid, pv1] + dg1_segments + obx_segments + pr1_segments
        
        return "\n".join(segments)
    
    def _create_msh_segment(self, message_type: str) -> str:
        """Create MSH (Message Header) segment."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        control_id = str(uuid.uuid4()).replace("-", "")[:10]
        
        return f"MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|{timestamp}||{message_type}|{control_id}|P|2.5.1"
    
    def _create_pid_segment(self, fhir_patient: Dict[str, Any]) -> str:
        """Create PID (Patient Identification) segment."""
        # Extract patient information
        patient_id = fhir_patient.get("id", "UNKNOWN")
        
        # Extract name
        names = fhir_patient.get("name", [])
        if names:
            name = names[0]
            family = name.get("family", "UNKNOWN")
            given = " ".join(name.get("given", ["UNKNOWN"]))
        else:
            family = "UNKNOWN"
            given = "UNKNOWN"
        
        # Extract birth date
        birth_date = fhir_patient.get("birthDate", "")
        if birth_date:
            birth_date = birth_date.replace("-", "")
        
        # Extract gender
        gender = fhir_patient.get("gender", "U").upper()
        
        # Extract address
        addresses = fhir_patient.get("address", [])
        if addresses:
            address = addresses[0]
            street = address.get("line", [""])[0]
            city = address.get("city", "")
            state = address.get("state", "")
            postal_code = address.get("postalCode", "")
            address_str = f"{street}^{city}^{state}^{postal_code}"
        else:
            address_str = "UNKNOWN"
        
        # Extract phone
        telecoms = fhir_patient.get("telecom", [])
        phone = ""
        for telecom in telecoms:
            if telecom.get("system") == "phone":
                phone = telecom.get("value", "")
                break
        
        # Create PID segment
        return (f"PID|1|{patient_id}|{patient_id}^^^SIMULATOR^MR~{patient_id}^^^SIMULATOR^SB|"
                f"{patient_id}^^^USSSA^SS|{family}^{given}||{birth_date}|{gender}|||"
                f"{address_str}||{phone}|||{gender}|NON|{patient_id}|{patient_id}")
    
    def _create_pv1_segment(self, fhir_patient: Dict[str, Any]) -> str:
        """Create PV1 (Patient Visit) segment."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate random provider info
        provider_id = str(uuid.uuid4()).replace("-", "")[:5]
        provider_name = f"PROVIDER^{random.choice(['JOHN', 'JANE', 'SMITH', 'JOHNSON'])}"
        
        return (f"PV1|1|I|MEDSURG^101^01||||{provider_id}^{provider_name}|||"
                f"GENERAL||||||ADM|A0|||||||||||||||||||||||||{timestamp}")
    
    def _create_dg1_segments(self, fhir_patient: Dict[str, Any], csv_data: Optional[Dict[str, List[Dict[str, Any]]]]) -> List[str]:
        """Create DG1 (Diagnosis) segments."""
        segments = []
        
        # Extract conditions from FHIR
        conditions = fhir_patient.get("extension", [])
        for ext in conditions:
            if ext.get("url") == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition":
                # Process condition
                pass
        
        # If no conditions found, generate some based on age/gender
        if not segments:
            age = self._calculate_age(fhir_patient.get("birthDate", ""))
            gender = fhir_patient.get("gender", "unknown")
            
            # Generate realistic diagnoses based on demographics
            if age > 65:
                segments.append("DG1|1|ICD-10-CM|I10|ESSENTIAL (PRIMARY) HYPERTENSION|20240101120000|A")
            if age > 50 and random.random() < 0.3:
                segments.append("DG1|2|ICD-10-CM|E11.9|TYPE 2 DIABETES MELLITUS WITHOUT COMPLICATIONS|20240101120000|A")
        
        return segments
    
    def _create_obx_segments(self, fhir_patient: Dict[str, Any], csv_data: Optional[Dict[str, List[Dict[str, Any]]]]) -> List[str]:
        """Create OBX (Observation Result) segments."""
        segments = []
        
        # Generate realistic vital signs
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        gender = fhir_patient.get("gender", "unknown")
        
        # Heart rate
        hr = random.randint(60, 100)
        if age > 65:
            hr = random.randint(70, 110)
        segments.append(f"OBX|1|NM|{self.loinc_codes['heart_rate']}^HEART RATE^LN||{hr}|/min|60-100|N|||F")
        
        # Blood pressure
        sys_bp = random.randint(110, 140)
        dia_bp = random.randint(70, 90)
        if age > 65:
            sys_bp = random.randint(120, 160)
            dia_bp = random.randint(75, 95)
        
        segments.append(f"OBX|2|NM|{self.loinc_codes['systolic_bp']}^SYSTOLIC BP^LN||{sys_bp}|mmHg|90-130|N|||F")
        segments.append(f"OBX|3|NM|{self.loinc_codes['diastolic_bp']}^DIASTOLIC BP^LN||{dia_bp}|mmHg|60-80|N|||F")
        
        # Temperature
        temp = round(random.uniform(36.5, 37.5), 1)
        segments.append(f"OBX|4|NM|{self.loinc_codes['temperature']}^BODY TEMPERATURE^LN||{temp}|C|36.5-37.5|N|||F")
        
        # Glucose
        glucose = random.randint(80, 120)
        if age > 50 and random.random() < 0.2:
            glucose = random.randint(140, 200)
        segments.append(f"OBX|5|NM|{self.loinc_codes['glucose']}^GLUCOSE^LN||{glucose}|mg/dL|70-110|N|||F")
        
        return segments
    
    def _create_pr1_segments(self, fhir_patient: Dict[str, Any], csv_data: Optional[Dict[str, List[Dict[str, Any]]]]) -> List[str]:
        """Create PR1 (Procedures) segments."""
        # For now, return empty list - procedures can be added based on specific scenarios
        return []
    
    def _calculate_age(self, birth_date: str) -> int:
        """Calculate age from birth date."""
        if not birth_date:
            return 30  # Default age
        
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return 30


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic patient data using Synthea")
    parser.add_argument("--num-patients", "-n", type=int, default=10, help="Number of patients to generate")
    parser.add_argument("--state", "-s", default="Massachusetts", help="US state for demographics")
    parser.add_argument("--city", "-c", default="Boston", help="City for demographics")
    parser.add_argument("--age-min", type=int, default=0, help="Minimum age")
    parser.add_argument("--age-max", type=int, default=100, help="Maximum age")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible results")
    parser.add_argument("--output-dir", "-o", default="synthea_output", help="Output directory")
    parser.add_argument("--convert-to-hl7", action="store_true", help="Convert generated data to HL7")
    
    args = parser.parse_args()
    
    # Generate patients
    generator = SyntheaGenerator(output_dir=args.output_dir)
    metadata = generator.generate_patients(
        num_patients=args.num_patients,
        state=args.state,
        city=args.city,
        age_min=args.age_min,
        age_max=args.age_max,
        seed=args.seed
    )
    
    print(f"Generated {metadata['fhir_files']} patients")
    print(f"Generation ID: {metadata['generation_id']}")
    
    # Convert to HL7 if requested
    if args.convert_to_hl7:
        converter = SyntheaToHL7Converter()
        patients = generator.get_fhir_patients(metadata['generation_id'])
        
        hl7_dir = Path(args.output_dir) / f"generation_{metadata['generation_id']}" / "hl7"
        hl7_dir.mkdir(exist_ok=True)
        
        for i, patient in enumerate(patients):
            hl7_message = converter.convert_patient_to_hl7(patient)
            
            patient_id = patient.get("id", f"patient_{i}")
            hl7_file = hl7_dir / f"{patient_id}.hl7"
            
            with open(hl7_file, "w") as f:
                f.write(hl7_message)
        
        print(f"Converted {len(patients)} patients to HL7 format")


if __name__ == "__main__":
    main()