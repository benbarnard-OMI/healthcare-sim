#!/usr/bin/env python3
"""
Synthea Scenario Loader for Healthcare Simulation

This module provides functionality to load and manage Synthea-generated patient scenarios
for use in healthcare simulations. It integrates with the existing scenario system while
providing access to realistic synthetic patient data.

Features:
- Load Synthea-generated FHIR data
- Convert to HL7 v2.x format
- Integrate with existing scenario system
- Support for dynamic scenario generation
- Realistic patient demographics and clinical data
"""

import json
import yaml
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from synthea_generator import SyntheaGenerator
from fhir_to_hl7_converter import FHIRToHL7Converter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheaScenarioLoader:
    """Loads and manages Synthea-generated patient scenarios."""
    
    def __init__(self, synthea_output_dir: str = "synthea_output", scenarios_config: str = "config/scenarios.yaml"):
        """
        Initialize the Synthea scenario loader.
        
        Args:
            synthea_output_dir: Directory containing Synthea-generated data
            scenarios_config: Path to scenarios configuration file
        """
        self.synthea_output_dir = Path(synthea_output_dir)
        self.scenarios_config = Path(scenarios_config)
        
        # Initialize converters
        self.synthea_generator = SyntheaGenerator(output_dir=str(self.synthea_output_dir))
        self.fhir_converter = FHIRToHL7Converter()
        
        # Load existing scenarios
        self.scenarios = self._load_existing_scenarios()
        
        # Cache for generated scenarios
        self._scenario_cache = {}
    
    def _load_existing_scenarios(self) -> Dict[str, Any]:
        """Load existing scenarios from configuration file."""
        if not self.scenarios_config.exists():
            logger.warning(f"Scenarios config not found: {self.scenarios_config}")
            return {}
        
        try:
            with open(self.scenarios_config, "r") as f:
                config = yaml.safe_load(f)
                return config.get("scenarios", {})
        except Exception as e:
            logger.error(f"Failed to load scenarios config: {e}")
            return {}
    
    def generate_synthea_scenarios(self, 
                                  num_patients: int = 20,
                                  age_min: int = 0,
                                  age_max: int = 100,
                                  state: str = "Massachusetts",
                                  city: str = "Boston",
                                  seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate new Synthea scenarios and integrate them into the simulation.
        
        Args:
            num_patients: Number of patients to generate
            age_min: Minimum age for generated patients
            age_max: Maximum age for generated patients
            state: US state for patient demographics
            city: City for patient demographics
            seed: Random seed for reproducible results
            
        Returns:
            Dictionary containing generation results and scenario metadata
        """
        logger.info(f"Generating {num_patients} Synthea patients...")
        
        # Generate patients using Synthea
        generation_metadata = self.synthea_generator.generate_patients(
            num_patients=num_patients,
            state=state,
            city=city,
            age_min=age_min,
            age_max=age_max,
            seed=seed
        )
        
        generation_id = generation_metadata["generation_id"]
        
        # Load FHIR patients
        fhir_patients = self.synthea_generator.get_fhir_patients(generation_id)
        
        # Convert to HL7 and create scenarios
        synthea_scenarios = {}
        
        for i, fhir_patient in enumerate(fhir_patients):
            try:
                # Convert to HL7
                hl7_message = self.fhir_converter.convert_patient_to_hl7(fhir_patient)
                
                # Create scenario metadata
                scenario_id = f"synthea_{generation_id}_{i+1}"
                scenario_name = self._generate_scenario_name(fhir_patient)
                
                # Determine clinical category and severity
                category, severity = self._classify_patient(fhir_patient)
                
                # Create scenario
                scenario = {
                    "name": scenario_name,
                    "description": f"Synthea-generated patient: {scenario_name}",
                    "category": category,
                    "severity": severity,
                    "tags": ["synthea", "generated", category],
                    "metadata": {
                        "generation_id": generation_id,
                        "patient_id": fhir_patient.get("id", f"patient_{i+1}"),
                        "age_group": self._get_age_group(fhir_patient),
                        "gender": fhir_patient.get("gender", "unknown"),
                        "primary_condition": self._get_primary_condition(fhir_patient),
                        "expected_duration": self._get_expected_duration(category, severity),
                        "synthea_generated": True,
                        "fhir_data": fhir_patient
                    },
                    "hl7_message": hl7_message,
                    "expected_findings": self._extract_expected_findings(fhir_patient),
                    "clinical_pathways": self._get_clinical_pathways(category, severity)
                }
                
                synthea_scenarios[scenario_id] = scenario
                
            except Exception as e:
                logger.error(f"Failed to process patient {i+1}: {e}")
                continue
        
        # Update scenarios configuration
        self.scenarios.update(synthea_scenarios)
        self._save_scenarios_config()
        
        logger.info(f"Successfully created {len(synthea_scenarios)} Synthea scenarios")
        
        return {
            "generation_metadata": generation_metadata,
            "scenarios_created": len(synthea_scenarios),
            "scenario_ids": list(synthea_scenarios.keys())
        }
    
    def _generate_scenario_name(self, fhir_patient: Dict[str, Any]) -> str:
        """Generate a descriptive name for the scenario."""
        # Extract patient name
        names = fhir_patient.get("name", [])
        if names:
            name = names[0]
            family = name.get("family", "")
            given = " ".join(name.get("given", []))
            patient_name = f"{given} {family}".strip()
        else:
            patient_name = "Unknown Patient"
        
        # Extract age
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        
        # Extract gender
        gender = fhir_patient.get("gender", "unknown")
        gender_display = {"male": "Male", "female": "Female", "other": "Other"}.get(gender, "Unknown")
        
        # Determine primary condition
        primary_condition = self._get_primary_condition(fhir_patient)
        
        return f"{patient_name} - {age}y/o {gender_display} with {primary_condition}"
    
    def _classify_patient(self, fhir_patient: Dict[str, Any]) -> Tuple[str, str]:
        """Classify patient into clinical category and severity."""
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        gender = fhir_patient.get("gender", "unknown")
        
        # Look for conditions in the patient data
        conditions = fhir_patient.get("extension", [])
        
        # Default classification
        category = "general_medicine"
        severity = "moderate"
        
        # Age-based classification
        if age < 18:
            category = "pediatrics"
            severity = "moderate"
        elif age > 65:
            category = "geriatrics"
            severity = "high"
        
        # Look for specific conditions
        for ext in conditions:
            if ext.get("url") == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition":
                condition = ext.get("valueCodeableConcept", {})
                coding = condition.get("coding", [])
                
                if coding:
                    condition_display = coding[0].get("display", "").lower()
                    
                    if any(keyword in condition_display for keyword in ["diabetes", "diabetic"]):
                        category = "endocrinology"
                        severity = "high"
                    elif any(keyword in condition_display for keyword in ["heart", "cardiac", "hypertension"]):
                        category = "cardiology"
                        severity = "high"
                    elif any(keyword in condition_display for keyword in ["stroke", "cerebral", "neurological"]):
                        category = "neurology"
                        severity = "critical"
                    elif any(keyword in condition_display for keyword in ["cancer", "tumor", "malignancy"]):
                        category = "oncology"
                        severity = "critical"
                    elif any(keyword in condition_display for keyword in ["pneumonia", "respiratory", "asthma"]):
                        category = "pulmonology"
                        severity = "moderate"
                    elif any(keyword in condition_display for keyword in ["fracture", "surgery", "orthopedic"]):
                        category = "orthopedics"
                        severity = "high"
                    elif any(keyword in condition_display for keyword in ["depression", "anxiety", "mental"]):
                        category = "psychiatry"
                        severity = "moderate"
        
        return category, severity
    
    def _get_age_group(self, fhir_patient: Dict[str, Any]) -> str:
        """Determine age group for the patient."""
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        
        if age < 2:
            return "infant"
        elif age < 12:
            return "pediatric"
        elif age < 18:
            return "adolescent"
        elif age < 65:
            return "adult"
        else:
            return "elderly"
    
    def _get_primary_condition(self, fhir_patient: Dict[str, Any]) -> str:
        """Determine the primary condition for the patient."""
        # Look for conditions
        conditions = fhir_patient.get("extension", [])
        
        for ext in conditions:
            if ext.get("url") == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition":
                condition = ext.get("valueCodeableConcept", {})
                coding = condition.get("coding", [])
                
                if coding:
                    return coding[0].get("display", "Unknown Condition")
        
        # Default based on age
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        if age < 5:
            return "pediatric_condition"
        elif age > 65:
            return "geriatric_condition"
        else:
            return "adult_condition"
    
    def _get_expected_duration(self, category: str, severity: str) -> str:
        """Determine expected care duration based on category and severity."""
        duration_map = {
            ("pediatrics", "low"): "1-2_days",
            ("pediatrics", "moderate"): "2-3_days",
            ("pediatrics", "high"): "3-5_days",
            ("pediatrics", "critical"): "5-10_days",
            
            ("cardiology", "moderate"): "2-4_days",
            ("cardiology", "high"): "4-7_days",
            ("cardiology", "critical"): "7-14_days",
            
            ("neurology", "moderate"): "3-5_days",
            ("neurology", "high"): "5-10_days",
            ("neurology", "critical"): "10-21_days",
            
            ("oncology", "high"): "7-14_days",
            ("oncology", "critical"): "14-30_days",
            
            ("orthopedics", "high"): "3-7_days",
            ("orthopedics", "critical"): "7-14_days",
            
            ("general_medicine", "low"): "1-2_days",
            ("general_medicine", "moderate"): "2-4_days",
            ("general_medicine", "high"): "4-7_days"
        }
        
        return duration_map.get((category, severity), "2-5_days")
    
    def _extract_expected_findings(self, fhir_patient: Dict[str, Any]) -> List[str]:
        """Extract expected clinical findings from patient data."""
        findings = []
        
        # Look for observations
        conditions = fhir_patient.get("extension", [])
        
        for ext in conditions:
            if ext.get("url") == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition":
                condition = ext.get("valueCodeableConcept", {})
                coding = condition.get("coding", [])
                
                if coding:
                    condition_display = coding[0].get("display", "").lower()
                    
                    if "diabetes" in condition_display:
                        findings.extend(["hyperglycemia", "elevated_hba1c"])
                    elif "hypertension" in condition_display:
                        findings.append("elevated_blood_pressure")
                    elif "heart" in condition_display or "cardiac" in condition_display:
                        findings.extend(["elevated_heart_rate", "abnormal_ekg"])
                    elif "stroke" in condition_display:
                        findings.extend(["neurological_deficit", "abnormal_imaging"])
                    elif "pneumonia" in condition_display:
                        findings.extend(["elevated_temperature", "abnormal_chest_xray"])
        
        # Add age-based findings
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        if age > 65:
            findings.extend(["age_related_changes", "multiple_comorbidities"])
        elif age < 5:
            findings.extend(["pediatric_vital_signs", "growth_parameters"])
        
        return findings if findings else ["routine_findings"]
    
    def _get_clinical_pathways(self, category: str, severity: str) -> List[str]:
        """Get appropriate clinical pathways based on category and severity."""
        pathway_map = {
            "cardiology": ["cardiac_workup", "ekg_monitoring", "troponin_testing", "echocardiogram"],
            "endocrinology": ["diabetes_management", "glucose_monitoring", "medication_adjustment"],
            "neurology": ["neurological_assessment", "imaging_studies", "neurological_monitoring"],
            "oncology": ["cancer_staging", "treatment_planning", "symptom_management"],
            "orthopedics": ["pre_operative_assessment", "surgical_procedure", "post_operative_care"],
            "pediatrics": ["pediatric_assessment", "growth_monitoring", "family_education"],
            "psychiatry": ["mental_health_assessment", "medication_management", "therapy_sessions"],
            "pulmonology": ["respiratory_assessment", "chest_imaging", "oxygen_therapy"],
            "geriatrics": ["comprehensive_geriatric_assessment", "fall_risk_assessment", "medication_review"],
            "general_medicine": ["general_assessment", "routine_monitoring", "preventive_care"]
        }
        
        base_pathways = pathway_map.get(category, ["general_assessment", "routine_monitoring"])
        
        # Add severity-specific pathways
        if severity == "critical":
            base_pathways.extend(["intensive_monitoring", "emergency_protocols"])
        elif severity == "high":
            base_pathways.extend(["close_monitoring", "specialized_care"])
        
        return base_pathways
    
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
    
    def _save_scenarios_config(self):
        """Save updated scenarios to configuration file."""
        try:
            # Load existing config
            if self.scenarios_config.exists():
                with open(self.scenarios_config, "r") as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Update scenarios
            config["scenarios"] = self.scenarios
            
            # Save updated config
            with open(self.scenarios_config, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Updated scenarios configuration: {self.scenarios_config}")
            
        except Exception as e:
            logger.error(f"Failed to save scenarios config: {e}")
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scenario by ID."""
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[str]:
        """
        List available scenarios with optional filtering.
        
        Args:
            category: Filter by clinical category
            tags: Filter by tags
            
        Returns:
            List of scenario IDs
        """
        scenario_ids = []
        
        for scenario_id, scenario in self.scenarios.items():
            # Filter by category
            if category and scenario.get("category") != category:
                continue
            
            # Filter by tags
            if tags:
                scenario_tags = scenario.get("tags", [])
                if not any(tag in scenario_tags for tag in tags):
                    continue
            
            scenario_ids.append(scenario_id)
        
        return sorted(scenario_ids)
    
    def get_hl7_message(self, scenario_id: str) -> Optional[str]:
        """Get HL7 message for a specific scenario."""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return scenario.get("hl7_message")
        return None
    
    def get_synthea_scenarios(self) -> List[str]:
        """Get all Synthea-generated scenarios."""
        return [scenario_id for scenario_id, scenario in self.scenarios.items() 
                if scenario.get("metadata", {}).get("synthea_generated", False)]
    
    def refresh_scenarios(self):
        """Refresh scenarios from configuration file."""
        self.scenarios = self._load_existing_scenarios()
        logger.info(f"Refreshed {len(self.scenarios)} scenarios")
    
    def export_scenario(self, scenario_id: str, output_file: str):
        """Export a scenario to a file."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        with open(output_file, "w") as f:
            f.write(scenario["hl7_message"])
        
        logger.info(f"Exported scenario {scenario_id} to {output_file}")
    
    def export_all_synthea_scenarios(self, output_dir: str):
        """Export all Synthea scenarios to individual files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        synthea_scenarios = self.get_synthea_scenarios()
        
        for scenario_id in synthea_scenarios:
            scenario = self.get_scenario(scenario_id)
            if scenario:
                filename = f"{scenario_id}.hl7"
                filepath = output_path / filename
                
                with open(filepath, "w") as f:
                    f.write(scenario["hl7_message"])
        
        logger.info(f"Exported {len(synthea_scenarios)} Synthea scenarios to {output_dir}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Synthea scenarios for healthcare simulation")
    parser.add_argument("--generate", "-g", action="store_true", help="Generate new Synthea scenarios")
    parser.add_argument("--num-patients", "-n", type=int, default=20, help="Number of patients to generate")
    parser.add_argument("--age-min", type=int, default=0, help="Minimum age")
    parser.add_argument("--age-max", type=int, default=100, help="Maximum age")
    parser.add_argument("--state", "-s", default="Massachusetts", help="US state")
    parser.add_argument("--city", "-c", default="Boston", help="City")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--list", "-l", action="store_true", help="List available scenarios")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--tags", nargs="+", help="Filter by tags")
    parser.add_argument("--export", "-e", help="Export scenario to file")
    parser.add_argument("--export-all", help="Export all Synthea scenarios to directory")
    parser.add_argument("--scenario-id", help="Scenario ID for export")
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = SyntheaScenarioLoader()
    
    if args.generate:
        # Generate new scenarios
        result = loader.generate_synthea_scenarios(
            num_patients=args.num_patients,
            age_min=args.age_min,
            age_max=args.age_max,
            state=args.state,
            city=args.city,
            seed=args.seed
        )
        print(f"Generated {result['scenarios_created']} scenarios")
        print(f"Generation ID: {result['generation_metadata']['generation_id']}")
    
    elif args.list:
        # List scenarios
        scenarios = loader.list_scenarios(category=args.category, tags=args.tags)
        print(f"Found {len(scenarios)} scenarios:")
        for scenario_id in scenarios:
            scenario = loader.get_scenario(scenario_id)
            print(f"  {scenario_id}: {scenario['name']} ({scenario['category']}, {scenario['severity']})")
    
    elif args.export:
        # Export single scenario
        if not args.scenario_id:
            print("Error: --scenario-id required for export")
            return
        
        loader.export_scenario(args.scenario_id, args.export)
        print(f"Exported scenario {args.scenario_id} to {args.export}")
    
    elif args.export_all:
        # Export all Synthea scenarios
        loader.export_all_synthea_scenarios(args.export_all)
        print(f"Exported all Synthea scenarios to {args.export_all}")
    
    else:
        print("Use --help for available options")


if __name__ == "__main__":
    main()