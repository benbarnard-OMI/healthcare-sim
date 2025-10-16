#!/usr/bin/env python3
"""
Test script for HL7 validation and FHIR generation capabilities.
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from hl7_validator import validate_hl7_message, ValidationLevel
from tools.healthcare_tools import HL7ValidationTool, FHIRGenerationTool
from crew import HealthcareSimulationCrew

def test_hl7_validation():
    """Test HL7 message validation."""
    print("🔍 Testing HL7 Message Validation")
    print("=" * 50)
    
    # Sample HL7 message with some issues
    sample_hl7 = """MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000
DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A
OBX|1|NM|8867-4^HEART RATE^LN||88|/min|60-100|N|||F
OBX|2|NM|8480-6^SYSTOLIC BP^LN||142|mmHg|90-130|H|||F"""
    
    # Test with different validation levels
    for level_name, level in [("Basic", ValidationLevel.BASIC), ("Standard", ValidationLevel.STANDARD), ("Strict", ValidationLevel.STRICT)]:
        print(f"\n--- {level_name} Validation ---")
        result = validate_hl7_message(sample_hl7, level)
        
        print(f"Status: {result['status']}")
        print(f"Total Issues: {result['total_issues']}")
        print(f"Severity Counts: {result['severity_counts']}")
        
        if result['issues']:
            print("Issues found:")
            for issue in result['issues'][:3]:  # Show first 3 issues
                print(f"  - {issue['severity']}: {issue['message']}")
            if len(result['issues']) > 3:
                print(f"  ... and {len(result['issues']) - 3} more issues")
    
    # Test with invalid HL7 message
    print(f"\n--- Testing Invalid HL7 Message ---")
    invalid_hl7 = "This is not a valid HL7 message"
    result = validate_hl7_message(invalid_hl7, ValidationLevel.STANDARD)
    print(f"Status: {result['status']}")
    print(f"Total Issues: {result['total_issues']}")

def test_fhir_generation():
    """Test FHIR generation from patient data."""
    print("\n🎯 Testing FHIR Generation")
    print("=" * 50)
    
    # Sample patient data
    patient_data = {
        'id': 'PATIENT123',
        'family_name': 'Smith',
        'given_name': 'John',
        'birth_date': '1965-03-12',
        'gender': 'male',
        'phone': '555-555-5555',
        'address': {
            'line': ['123 Main St'],
            'city': 'Boston',
            'state': 'MA',
            'postalCode': '02115',
            'country': 'US'
        },
        'visit_info': {
            'patient_class': 'inpatient',
            'assigned_patient_location': 'MEDSURG-101-01',
            'admit_date_time': '2024-01-01T12:00:00Z'
        },
        'diagnoses': [
            {
                'code': 'R07.9',
                'description': 'Chest pain, unspecified',
                'date': '2024-01-01T12:00:00Z'
            }
        ],
        'observations': [
            {
                'observation_identifier': '8867-4',
                'observation_description': 'Heart rate',
                'observation_value': '88',
                'units': '/min',
                'reference_range': '60-100'
            },
            {
                'observation_identifier': '8480-6',
                'observation_description': 'Systolic blood pressure',
                'observation_value': '142',
                'units': 'mmHg',
                'reference_range': '90-130'
            }
        ],
        'procedures': [
            {
                'procedure_code': '81.51',
                'procedure_description': 'Total hip replacement',
                'procedure_date_time': '2024-01-02T08:00:00Z',
                'surgeon_name': 'Dr. Rodriguez'
            }
        ]
    }
    
    # Test FHIR generation
    fhir_tool = FHIRGenerationTool()
    
    print("--- Generating FHIR Bundle ---")
    result = fhir_tool._run(patient_data, "bundle", generate_hl7=True)
    print(result)
    
    print("\n--- Generating Individual Resources ---")
    result = fhir_tool._run(patient_data, "individual_resources", generate_hl7=False)
    print(result)

def test_crew_integration():
    """Test integration with HealthcareSimulationCrew."""
    print("\n🏥 Testing Crew Integration")
    print("=" * 50)
    
    try:
        # Initialize crew
        crew = HealthcareSimulationCrew()
        
        # Test HL7 validation tool
        print("--- Testing HL7 Validation Tool ---")
        hl7_tool = crew.healthcare_tools.hl7_validation_tool()
        
        sample_hl7 = """MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR||SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A"""
        
        validation_result = hl7_tool._run(sample_hl7, "standard")
        print(validation_result)
        
        # Test FHIR generation tool
        print("\n--- Testing FHIR Generation Tool ---")
        fhir_tool = crew.healthcare_tools.fhir_generation_tool()
        
        patient_data = {
            'id': 'TEST123',
            'family_name': 'Doe',
            'given_name': 'Jane',
            'birth_date': '1980-01-01',
            'gender': 'female',
            'diagnoses': [{'code': 'E11.9', 'description': 'Type 2 diabetes mellitus'}],
            'observations': [{'observation_identifier': '2345-7', 'observation_description': 'Glucose', 'observation_value': '120', 'units': 'mg/dL'}]
        }
        
        fhir_result = fhir_tool._run(patient_data, "summary", generate_hl7=True)
        print(fhir_result)
        
    except Exception as e:
        print(f"Error testing crew integration: {e}")

def main():
    """Run all tests."""
    print("🧪 HL7 Validation and FHIR Generation Test Suite")
    print("=" * 60)
    
    try:
        test_hl7_validation()
        test_fhir_generation()
        test_crew_integration()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()