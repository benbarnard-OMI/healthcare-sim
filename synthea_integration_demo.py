#!/usr/bin/env python3
"""
Synthea Integration Demo for Healthcare Simulation

This script demonstrates how to use Synthea-generated synthetic patient data
with the healthcare simulation system. It shows the complete workflow from
generating realistic patient data to running simulations.

Usage:
    python synthea_integration_demo.py --help
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthea_generator import SyntheaGenerator
from fhir_to_hl7_converter import FHIRToHL7Converter
from synthea_scenario_loader import SyntheaScenarioLoader
from scenario_loader import get_scenario_loader
from crew import HealthcareSimulationCrew
from llm_config import create_llm_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyntheaIntegrationDemo:
    """Demonstrates Synthea integration with healthcare simulation."""
    
    def __init__(self, output_dir: str = "synthea_demo_output"):
        """Initialize the demo."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.synthea_generator = SyntheaGenerator(output_dir=str(self.output_dir / "synthea_data"))
        self.fhir_converter = FHIRToHL7Converter()
        self.scenario_loader = SyntheaScenarioLoader(
            synthea_output_dir=str(self.output_dir / "synthea_data"),
            scenarios_config="config/scenarios.yaml"
        )
    
    def generate_diverse_patients(self, 
                                 num_patients: int = 50,
                                 age_ranges: List[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Generate a diverse set of patients covering different age groups and conditions.
        
        Args:
            num_patients: Total number of patients to generate
            age_ranges: List of (min_age, max_age) tuples for different groups
            
        Returns:
            Dictionary containing generation results
        """
        if age_ranges is None:
            age_ranges = [
                (0, 5),      # Infants and toddlers
                (6, 17),     # Children and adolescents
                (18, 35),    # Young adults
                (36, 55),    # Middle-aged adults
                (56, 75),    # Older adults
                (76, 100)    # Elderly
            ]
        
        logger.info(f"Generating {num_patients} diverse patients...")
        
        # Calculate patients per age group
        patients_per_group = num_patients // len(age_ranges)
        remaining_patients = num_patients % len(age_ranges)
        
        all_results = []
        
        for i, (min_age, max_age) in enumerate(age_ranges):
            group_patients = patients_per_group + (1 if i < remaining_patients else 0)
            
            if group_patients == 0:
                continue
            
            logger.info(f"Generating {group_patients} patients aged {min_age}-{max_age}")
            
            try:
                result = self.synthea_generator.generate_patients(
                    num_patients=group_patients,
                    age_min=min_age,
                    age_max=max_age,
                    state="Massachusetts",
                    city="Boston",
                    seed=42 + i  # Different seed for each group
                )
                all_results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to generate patients for age group {min_age}-{max_age}: {e}")
                continue
        
        # Combine results
        total_patients = sum(r.get('fhir_files', 0) for r in all_results)
        logger.info(f"Successfully generated {total_patients} patients across {len(age_ranges)} age groups")
        
        return {
            "total_patients": total_patients,
            "age_groups": len(age_ranges),
            "generations": all_results
        }
    
    def create_realistic_scenarios(self, generation_ids: List[str]) -> Dict[str, Any]:
        """
        Create realistic healthcare scenarios from Synthea-generated patients.
        
        Args:
            generation_ids: List of generation IDs to process
            
        Returns:
            Dictionary containing scenario creation results
        """
        logger.info(f"Creating scenarios from {len(generation_ids)} generations...")
        
        total_scenarios = 0
        scenario_categories = {}
        
        for generation_id in generation_ids:
            try:
                # Load FHIR patients
                fhir_patients = self.synthea_generator.get_fhir_patients(generation_id)
                
                # Convert to scenarios
                for i, fhir_patient in enumerate(fhir_patients):
                    try:
                        # Convert to HL7
                        hl7_message = self.fhir_converter.convert_patient_to_hl7(fhir_patient)
                        
                        # Determine scenario characteristics
                        age = self._calculate_age(fhir_patient.get("birthDate", ""))
                        gender = fhir_patient.get("gender", "unknown")
                        
                        # Classify scenario
                        category, severity = self._classify_patient_scenario(fhir_patient, age, gender)
                        
                        # Track categories
                        if category not in scenario_categories:
                            scenario_categories[category] = 0
                        scenario_categories[category] += 1
                        
                        # Save scenario
                        scenario_id = f"synthea_{generation_id}_{i+1}"
                        scenario_file = self.output_dir / "scenarios" / f"{scenario_id}.hl7"
                        scenario_file.parent.mkdir(exist_ok=True)
                        
                        with open(scenario_file, "w") as f:
                            f.write(hl7_message)
                        
                        total_scenarios += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to process patient {i+1} from generation {generation_id}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Failed to process generation {generation_id}: {e}")
                continue
        
        logger.info(f"Created {total_scenarios} realistic scenarios")
        logger.info(f"Scenario categories: {scenario_categories}")
        
        return {
            "total_scenarios": total_scenarios,
            "categories": scenario_categories,
            "output_directory": str(self.output_dir / "scenarios")
        }
    
    def run_simulation_demo(self, 
                           scenario_id: str,
                           llm_backend: str = "openai",
                           api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a healthcare simulation using a Synthea-generated scenario.
        
        Args:
            scenario_id: ID of the scenario to simulate
            llm_backend: LLM backend to use
            api_key: API key for the LLM service
            
        Returns:
            Dictionary containing simulation results
        """
        logger.info(f"Running simulation for scenario: {scenario_id}")
        
        try:
            # Create LLM configuration
            llm_config = create_llm_config(
                backend=llm_backend,
                api_key=api_key,
                model="gpt-4" if llm_backend == "openai" else None
            )
            
            # Initialize simulation crew
            sim_crew = HealthcareSimulationCrew(llm_config=llm_config)
            
            # Get scenario data
            scenario_loader = get_scenario_loader()
            hl7_message = scenario_loader.get_hl7_message(scenario_id)
            
            if not hl7_message:
                raise ValueError(f"Scenario not found: {scenario_id}")
            
            # Run simulation
            logger.info("Starting healthcare simulation...")
            result = sim_crew.crew().kickoff(inputs={"hl7_message": hl7_message})
            
            # Save results
            results_file = self.output_dir / "simulation_results" / f"{scenario_id}_results.txt"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, "w") as f:
                if hasattr(result, 'raw'):
                    f.write(result.raw)
                else:
                    f.write(str(result))
            
            logger.info(f"Simulation completed. Results saved to: {results_file}")
            
            return {
                "scenario_id": scenario_id,
                "status": "success",
                "results_file": str(results_file),
                "simulation_output": str(result)
            }
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return {
                "scenario_id": scenario_id,
                "status": "failed",
                "error": str(e)
            }
    
    def demonstrate_full_workflow(self, 
                                 num_patients: int = 20,
                                 llm_backend: str = "openai",
                                 api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Demonstrate the complete Synthea integration workflow.
        
        Args:
            num_patients: Number of patients to generate
            llm_backend: LLM backend for simulation
            api_key: API key for LLM service
            
        Returns:
            Dictionary containing workflow results
        """
        logger.info("Starting Synthea integration demonstration...")
        
        workflow_results = {
            "step1_generation": None,
            "step2_scenarios": None,
            "step3_simulation": None,
            "overall_status": "in_progress"
        }
        
        try:
            # Step 1: Generate diverse patients
            logger.info("Step 1: Generating diverse patient population...")
            generation_result = self.generate_diverse_patients(num_patients)
            workflow_results["step1_generation"] = generation_result
            
            # Step 2: Create realistic scenarios
            logger.info("Step 2: Creating realistic healthcare scenarios...")
            generation_ids = [gen["generation_id"] for gen in generation_result["generations"]]
            scenario_result = self.create_realistic_scenarios(generation_ids)
            workflow_results["step2_scenarios"] = scenario_result
            
            # Step 3: Run simulation demo
            logger.info("Step 3: Running healthcare simulation...")
            if scenario_result["total_scenarios"] > 0:
                # Use the first scenario for demo
                demo_scenario = f"synthea_{generation_ids[0]}_1"
                simulation_result = self.run_simulation_demo(
                    demo_scenario, 
                    llm_backend, 
                    api_key
                )
                workflow_results["step3_simulation"] = simulation_result
            else:
                logger.warning("No scenarios created, skipping simulation")
                workflow_results["step3_simulation"] = {"status": "skipped", "reason": "no_scenarios"}
            
            workflow_results["overall_status"] = "completed"
            logger.info("Synthea integration demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            workflow_results["overall_status"] = "failed"
            workflow_results["error"] = str(e)
        
        return workflow_results
    
    def _calculate_age(self, birth_date: str) -> int:
        """Calculate age from birth date."""
        if not birth_date:
            return 30
        
        try:
            from datetime import datetime
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return 30
    
    def _classify_patient_scenario(self, fhir_patient: Dict[str, Any], age: int, gender: str) -> tuple:
        """Classify patient into scenario category and severity."""
        # Look for conditions
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
        
        return category, severity


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Synthea Integration Demo for Healthcare Simulation")
    parser.add_argument("--num-patients", "-n", type=int, default=20, help="Number of patients to generate")
    parser.add_argument("--llm-backend", "-b", default="openai", choices=["openai", "ollama", "openrouter"], 
                       help="LLM backend to use")
    parser.add_argument("--api-key", "-k", help="API key for LLM service")
    parser.add_argument("--output-dir", "-o", default="synthea_demo_output", help="Output directory")
    parser.add_argument("--demo-only", action="store_true", help="Run only the simulation demo")
    parser.add_argument("--scenario-id", help="Specific scenario ID for demo")
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = SyntheaIntegrationDemo(output_dir=args.output_dir)
    
    if args.demo_only:
        # Run only simulation demo
        if not args.scenario_id:
            logger.error("--scenario-id required for demo-only mode")
            return
        
        result = demo.run_simulation_demo(
            args.scenario_id,
            args.llm_backend,
            args.api_key
        )
        print(f"Simulation result: {result}")
    
    else:
        # Run full workflow
        result = demo.demonstrate_full_workflow(
            num_patients=args.num_patients,
            llm_backend=args.llm_backend,
            api_key=args.api_key
        )
        
        # Print summary
        print("\n" + "="*60)
        print("SYNTHEA INTEGRATION DEMO RESULTS")
        print("="*60)
        print(f"Overall Status: {result['overall_status']}")
        
        if result.get("step1_generation"):
            gen = result["step1_generation"]
            print(f"Patients Generated: {gen['total_patients']}")
            print(f"Age Groups: {gen['age_groups']}")
        
        if result.get("step2_scenarios"):
            scen = result["step2_scenarios"]
            print(f"Scenarios Created: {scen['total_scenarios']}")
            print(f"Categories: {scen['categories']}")
        
        if result.get("step3_simulation"):
            sim = result["step3_simulation"]
            print(f"Simulation Status: {sim['status']}")
            if sim.get("results_file"):
                print(f"Results File: {sim['results_file']}")
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        
        print("="*60)


if __name__ == "__main__":
    main()