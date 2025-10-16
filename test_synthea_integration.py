#!/usr/bin/env python3
"""
Test Script for Synthea Integration

This script validates the Synthea integration with the healthcare simulation system.
It tests all components including data generation, FHIR conversion, scenario loading,
and simulation integration.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthea_generator import SyntheaGenerator
from fhir_to_hl7_converter import FHIRToHL7Converter
from synthea_scenario_loader import SyntheaScenarioLoader
from scenario_loader import get_scenario_loader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyntheaIntegrationTester:
    """Tests Synthea integration components."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = {}
        self.temp_dir = None
    
    def setup_test_environment(self):
        """Set up temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="synthea_test_")
        logger.info(f"Test environment: {self.temp_dir}")
    
    def cleanup_test_environment(self):
        """Clean up temporary test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info("Test environment cleaned up")
    
    def test_synthea_generator(self) -> Dict[str, Any]:
        """Test Synthea data generation."""
        logger.info("Testing Synthea generator...")
        
        try:
            # Initialize generator
            generator = SyntheaGenerator(output_dir=os.path.join(self.temp_dir, "synthea_output"))
            
            # Generate small test dataset
            result = generator.generate_patients(
                num_patients=5,
                state="Massachusetts",
                city="Boston",
                age_min=20,
                age_max=60,
                seed=12345
            )
            
            # Validate generation
            assert result["fhir_files"] > 0, "No FHIR files generated"
            assert result["num_patients"] == 5, "Incorrect number of patients"
            
            # Test loading patients
            patients = generator.get_fhir_patients(result["generation_id"])
            assert len(patients) > 0, "No patients loaded"
            
            # Validate patient structure
            patient = patients[0]
            assert "id" in patient, "Patient missing ID"
            assert "name" in patient, "Patient missing name"
            assert "birthDate" in patient, "Patient missing birth date"
            assert "gender" in patient, "Patient missing gender"
            
            self.test_results["synthea_generator"] = {
                "status": "PASS",
                "patients_generated": result["fhir_files"],
                "generation_id": result["generation_id"]
            }
            
            logger.info("✓ Synthea generator test passed")
            return result
            
        except Exception as e:
            self.test_results["synthea_generator"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"✗ Synthea generator test failed: {e}")
            raise
    
    def test_fhir_to_hl7_converter(self, generation_id: str) -> Dict[str, Any]:
        """Test FHIR to HL7 conversion."""
        logger.info("Testing FHIR to HL7 converter...")
        
        try:
            # Initialize converter
            converter = FHIRToHL7Converter()
            
            # Initialize generator to load patients
            generator = SyntheaGenerator(output_dir=os.path.join(self.temp_dir, "synthea_output"))
            patients = generator.get_fhir_patients(generation_id)
            
            assert len(patients) > 0, "No patients available for conversion"
            
            # Test conversion
            patient = patients[0]
            hl7_message = converter.convert_patient_to_hl7(patient)
            
            # Validate HL7 message
            assert hl7_message, "No HL7 message generated"
            assert "MSH|" in hl7_message, "Missing MSH segment"
            assert "PID|" in hl7_message, "Missing PID segment"
            assert "PV1|" in hl7_message, "Missing PV1 segment"
            
            # Check message structure
            lines = hl7_message.strip().split('\n')
            assert len(lines) >= 3, "Insufficient HL7 segments"
            
            # Validate field separators
            for line in lines:
                if line.startswith(('MSH', 'PID', 'PV1')):
                    assert '|' in line, f"Missing field separator in {line[:3]}"
            
            self.test_results["fhir_to_hl7_converter"] = {
                "status": "PASS",
                "hl7_message_length": len(hl7_message),
                "segments_count": len(lines)
            }
            
            logger.info("✓ FHIR to HL7 converter test passed")
            return {"hl7_message": hl7_message, "patients": patients}
            
        except Exception as e:
            self.test_results["fhir_to_hl7_converter"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"✗ FHIR to HL7 converter test failed: {e}")
            raise
    
    def test_synthea_scenario_loader(self, generation_id: str) -> Dict[str, Any]:
        """Test Synthea scenario loader."""
        logger.info("Testing Synthea scenario loader...")
        
        try:
            # Initialize loader
            loader = SyntheaScenarioLoader(
                synthea_output_dir=os.path.join(self.temp_dir, "synthea_output"),
                scenarios_config=os.path.join(self.temp_dir, "scenarios.yaml")
            )
            
            # Generate scenarios
            result = loader.generate_synthea_scenarios(
                num_patients=3,
                age_min=25,
                age_max=45,
                state="Massachusetts",
                city="Boston",
                seed=54321
            )
            
            # Validate scenario generation
            assert result["scenarios_created"] > 0, "No scenarios created"
            assert len(result["scenario_ids"]) > 0, "No scenario IDs returned"
            
            # Test scenario retrieval
            scenario_id = result["scenario_ids"][0]
            scenario = loader.get_scenario(scenario_id)
            
            assert scenario, "Scenario not found"
            assert "name" in scenario, "Scenario missing name"
            assert "hl7_message" in scenario, "Scenario missing HL7 message"
            assert "category" in scenario, "Scenario missing category"
            assert "severity" in scenario, "Scenario missing severity"
            
            # Test HL7 message retrieval
            hl7_message = loader.get_hl7_message(scenario_id)
            assert hl7_message, "HL7 message not retrieved"
            assert "MSH|" in hl7_message, "Invalid HL7 message"
            
            # Test scenario listing
            all_scenarios = loader.list_scenarios()
            assert len(all_scenarios) > 0, "No scenarios listed"
            assert scenario_id in all_scenarios, "Generated scenario not in list"
            
            # Test Synthea-specific scenarios
            synthea_scenarios = loader.get_synthea_scenarios()
            assert len(synthea_scenarios) > 0, "No Synthea scenarios found"
            
            self.test_results["synthea_scenario_loader"] = {
                "status": "PASS",
                "scenarios_created": result["scenarios_created"],
                "scenario_ids": result["scenario_ids"]
            }
            
            logger.info("✓ Synthea scenario loader test passed")
            return result
            
        except Exception as e:
            self.test_results["synthea_scenario_loader"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"✗ Synthea scenario loader test failed: {e}")
            raise
    
    def test_integrated_scenario_loader(self) -> Dict[str, Any]:
        """Test integrated scenario loader with Synthea support."""
        logger.info("Testing integrated scenario loader...")
        
        try:
            # Initialize integrated loader
            loader = get_scenario_loader(enable_synthea=True)
            
            # Test scenario listing
            all_scenarios = loader.list_scenarios()
            assert len(all_scenarios) > 0, "No scenarios available"
            
            # Test Synthea scenario generation
            synthea_result = loader.generate_synthea_scenarios(
                num_patients=2,
                age_min=30,
                age_max=50,
                state="Massachusetts",
                city="Boston",
                seed=98765
            )
            
            assert synthea_result["scenarios_created"] > 0, "No Synthea scenarios created"
            
            # Test scenario retrieval
            scenario_id = synthea_result["scenario_ids"][0]
            scenario = loader.get_scenario(scenario_id)
            
            assert scenario, "Generated scenario not found"
            assert scenario.hl7_message, "Scenario missing HL7 message"
            
            # Test HL7 message retrieval
            hl7_message = loader.get_hl7_message(scenario_id)
            assert hl7_message, "HL7 message not retrieved"
            
            # Test Synthea-specific functionality
            synthea_scenarios = loader.get_synthea_scenarios()
            assert len(synthea_scenarios) > 0, "No Synthea scenarios found"
            
            self.test_results["integrated_scenario_loader"] = {
                "status": "PASS",
                "total_scenarios": len(all_scenarios),
                "synthea_scenarios": len(synthea_scenarios)
            }
            
            logger.info("✓ Integrated scenario loader test passed")
            return synthea_result
            
        except Exception as e:
            self.test_results["integrated_scenario_loader"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"✗ Integrated scenario loader test failed: {e}")
            raise
    
    def test_hl7_message_validation(self, hl7_message: str) -> Dict[str, Any]:
        """Test HL7 message validation."""
        logger.info("Testing HL7 message validation...")
        
        try:
            # Basic structure validation
            lines = hl7_message.strip().split('\n')
            assert len(lines) >= 3, "Insufficient HL7 segments"
            
            # Check required segments
            segment_types = [line.split('|')[0] for line in lines if line.strip()]
            assert 'MSH' in segment_types, "Missing MSH segment"
            assert 'PID' in segment_types, "Missing PID segment"
            
            # Validate MSH segment
            msh_line = next(line for line in lines if line.startswith('MSH|'))
            msh_fields = msh_line.split('|')
            assert len(msh_fields) >= 12, "MSH segment incomplete"
            assert msh_fields[1] == '^~\\&', "Invalid field separators"
            
            # Validate PID segment
            pid_line = next(line for line in lines if line.startswith('PID|'))
            pid_fields = pid_line.split('|')
            assert len(pid_fields) >= 20, "PID segment incomplete"
            
            # Check for patient name
            patient_name = pid_fields[5] if len(pid_fields) > 5 else ""
            assert patient_name and patient_name != "", "Missing patient name"
            
            # Check for birth date
            birth_date = pid_fields[7] if len(pid_fields) > 7 else ""
            assert birth_date and birth_date != "", "Missing birth date"
            
            # Check for gender
            gender = pid_fields[8] if len(pid_fields) > 8 else ""
            assert gender and gender in ['M', 'F', 'O', 'U'], "Invalid gender"
            
            self.test_results["hl7_validation"] = {
                "status": "PASS",
                "segments_count": len(lines),
                "segment_types": segment_types
            }
            
            logger.info("✓ HL7 message validation test passed")
            return {"valid": True, "segments": len(lines)}
            
        except Exception as e:
            self.test_results["hl7_validation"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"✗ HL7 message validation test failed: {e}")
            raise
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("Starting Synthea integration tests...")
        
        try:
            self.setup_test_environment()
            
            # Test 1: Synthea Generator
            generation_result = self.test_synthea_generator()
            generation_id = generation_result["generation_id"]
            
            # Test 2: FHIR to HL7 Converter
            conversion_result = self.test_fhir_to_hl7_converter(generation_id)
            hl7_message = conversion_result["hl7_message"]
            
            # Test 3: HL7 Message Validation
            self.test_hl7_message_validation(hl7_message)
            
            # Test 4: Synthea Scenario Loader
            self.test_synthea_scenario_loader(generation_id)
            
            # Test 5: Integrated Scenario Loader
            self.test_integrated_scenario_loader()
            
            # Calculate overall results
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
            failed_tests = total_tests - passed_tests
            
            overall_status = "PASS" if failed_tests == 0 else "FAIL"
            
            test_summary = {
                "overall_status": overall_status,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "test_results": self.test_results
            }
            
            logger.info(f"Integration tests completed: {passed_tests}/{total_tests} passed")
            
            return test_summary
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return {
                "overall_status": "FAIL",
                "error": str(e),
                "test_results": self.test_results
            }
        
        finally:
            self.cleanup_test_environment()
    
    def print_test_results(self, results: Dict[str, Any]):
        """Print test results in a formatted way."""
        print("\n" + "="*60)
        print("SYNTHEA INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Overall Status: {results['overall_status']}")
        print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
        
        if results.get('failed_tests', 0) > 0:
            print(f"Tests Failed: {results['failed_tests']}")
        
        print("\nDetailed Results:")
        print("-" * 40)
        
        for test_name, result in results['test_results'].items():
            status_icon = "✓" if result['status'] == "PASS" else "✗"
            print(f"{status_icon} {test_name}: {result['status']}")
            
            if result['status'] == "FAIL" and 'error' in result:
                print(f"    Error: {result['error']}")
            elif result['status'] == "PASS":
                # Print additional details for passed tests
                for key, value in result.items():
                    if key != 'status':
                        print(f"    {key}: {value}")
        
        print("="*60)


def main():
    """Main function for running tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Synthea Integration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Output file for test results")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    tester = SyntheaIntegrationTester()
    results = tester.run_all_tests()
    
    # Print results
    tester.print_test_results(results)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nTest results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'PASS' else 1)


if __name__ == "__main__":
    main()