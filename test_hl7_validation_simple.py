#!/usr/bin/env python3
"""
Simple test script for HL7 validation capabilities.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_hl7_validation():
    """Test HL7 message validation."""
    print("🔍 Testing HL7 Message Validation")
    print("=" * 50)
    
    try:
        from hl7_validator import validate_hl7_message, ValidationLevel
        
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
        
        print("\n✅ HL7 validation test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fhir_converter():
    """Test FHIR converter functionality."""
    print("\n🎯 Testing FHIR Converter")
    print("=" * 50)
    
    try:
        from fhir_to_hl7_converter import FHIRToHL7Converter
        
        # Create sample FHIR Bundle
        sample_fhir_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-123",
            "type": "collection",
            "timestamp": "2024-01-01T12:00:00Z",
            "entry": [
                {
                    "fullUrl": "urn:uuid:patient-123",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-123",
                        "identifier": [{
                            "use": "usual",
                            "type": {
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                    "code": "MR",
                                    "display": "Medical Record Number"
                                }]
                            },
                            "value": "12345"
                        }],
                        "name": [{
                            "use": "official",
                            "family": "Smith",
                            "given": ["John"]
                        }],
                        "gender": "male",
                        "birthDate": "1965-03-12"
                    }
                }
            ]
        }
        
        # Test conversion
        converter = FHIRToHL7Converter()
        hl7_messages = converter.convert_bundle_to_hl7(sample_fhir_bundle)
        
        print(f"✅ Successfully converted FHIR Bundle to {len(hl7_messages)} HL7 message(s)")
        if hl7_messages:
            print("Sample HL7 message:")
            print(hl7_messages[0][:200] + "..." if len(hl7_messages[0]) > 200 else hl7_messages[0])
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 HL7 Validation and FHIR Converter Test Suite")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    if test_hl7_validation():
        success_count += 1
    
    if test_fhir_converter():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()