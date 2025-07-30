import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the Python path to import crew module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from crew import HealthcareSimulationCrew, UNKNOWN_PATIENT_ID
    from sample_data.sample_messages import SAMPLE_MESSAGES
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import failed: {e}")
    IMPORTS_AVAILABLE = False

class TestEnhancedHL7Parsing(unittest.TestCase):
    """Test enhanced HL7 parsing functionality with support for additional segments."""
    
    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        self.sim_crew = HealthcareSimulationCrew()

    def test_comprehensive_parsing_chest_pain(self):
        """Test comprehensive parsing of chest pain sample message."""
        inputs = {'hl7_message': SAMPLE_MESSAGES['chest_pain']}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Verify patient info
        self.assertIn('patient_id', result)
        self.assertIn('patient_info', result)
        self.assertEqual(result['patient_id'], '12345')
        
        # Verify comprehensive patient data
        patient_info = result['patient_info']
        self.assertEqual(patient_info['id'], '12345')
        self.assertIn('SMITH', patient_info['name'])
        self.assertIn('JOHN', patient_info['name'])
        self.assertEqual(patient_info['gender'], 'M')
        
        # Verify diagnoses
        self.assertIn('diagnoses', result)
        self.assertGreater(len(result['diagnoses']), 0)
        diagnosis = result['diagnoses'][0]
        self.assertEqual(diagnosis['code'], 'R07.9')
        self.assertIn('CHEST PAIN', diagnosis['description'])
        
        # Verify observations (OBX segments)
        self.assertIn('observations', result)
        self.assertGreater(len(result['observations']), 0)
        
        # Find heart rate observation
        heart_rate_obs = None
        for obs in result['observations']:
            if '8867-4' in obs.get('observation_identifier', ''):
                heart_rate_obs = obs
                break
        
        self.assertIsNotNone(heart_rate_obs, "Heart rate observation not found")
        self.assertEqual(heart_rate_obs['observation_value'], '88')
        self.assertEqual(heart_rate_obs['units'], '/min')
        
        # Verify visit info (PV1 segment)
        self.assertIn('visit_info', result)
        visit_info = result['visit_info']
        self.assertEqual(visit_info['patient_class'], 'I')
        self.assertEqual(visit_info['assigned_patient_location'], 'MEDSURG')
        
        # Verify parsing success
        self.assertTrue(result.get('parsing_success', False))

    def test_comprehensive_parsing_surgical_patient(self):
        """Test parsing of surgical patient with procedures (PR1 segment)."""
        inputs = {'hl7_message': SAMPLE_MESSAGES['surgical']}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Verify basic parsing
        self.assertEqual(result['patient_id'], '45678')
        
        # Verify procedures (PR1 segments)
        self.assertIn('procedures', result)
        self.assertGreater(len(result['procedures']), 0)
        
        procedure = result['procedures'][0]
        self.assertEqual(procedure['procedure_code'], '81.51')
        self.assertIn('HIP REPLACEMENT', procedure['procedure_description'])
        self.assertIn('RODRIGUEZ', procedure['surgeon_name'])

    def test_comprehensive_parsing_diabetes_patient(self):
        """Test parsing of diabetes patient with multiple diagnoses."""
        inputs = {'hl7_message': SAMPLE_MESSAGES['diabetes']}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Verify multiple diagnoses
        self.assertIn('diagnoses', result)
        self.assertGreaterEqual(len(result['diagnoses']), 3)
        
        # Check for diabetes diagnosis
        diabetes_found = False
        for diagnosis in result['diagnoses']:
            if 'E11.9' in diagnosis['code']:
                diabetes_found = True
                self.assertIn('DIABETES', diagnosis['description'])
                break
        self.assertTrue(diabetes_found, "Diabetes diagnosis not found")
        
        # Verify multiple observations including HbA1c
        hba1c_found = False
        for obs in result['observations']:
            if '4548-4' in obs.get('observation_identifier', ''):
                hba1c_found = True
                self.assertEqual(obs['observation_value'], '8.7')
                self.assertEqual(obs['units'], '%')
                break
        self.assertTrue(hba1c_found, "HbA1c observation not found")

    def test_validation_warnings_and_errors(self):
        """Test validation warnings and error reporting."""
        # Test with incomplete HL7 message
        incomplete_message = """
MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR||||||||||||||||
"""
        inputs = {'hl7_message': incomplete_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should have validation warnings for missing patient data
        self.assertIn('validation_errors', result)
        self.assertGreater(result.get('validation_warnings', 0), 0)
        
        # Check for specific validation warnings
        validation_errors = result['validation_errors']
        warning_found = False
        for error in validation_errors:
            if 'ValidationWarning' in error['error_type'] and 'name' in error['message']:
                warning_found = True
                break
        self.assertTrue(warning_found, "Patient name validation warning not found")

    def test_malformed_message_handling(self):
        """Test handling of completely malformed messages."""
        malformed_message = "This is not an HL7 message at all!"
        inputs = {'hl7_message': malformed_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should fall back to UNKNOWN_PATIENT_ID
        self.assertEqual(result['patient_id'], UNKNOWN_PATIENT_ID)
        self.assertIn('validation_errors', result)
        self.assertFalse(result.get('parsing_success', True))

    def test_missing_segments_handling(self):
        """Test handling of messages with missing segments."""
        # Message with only MSH and PID
        minimal_message = """
MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|54321|54321^^^SIMULATOR^MR~3333^^^SIMULATOR^SB|8888888888^^^USSSA^SS|DOE^JANE^F||19900101|F|||456 TEST ST^^CITY^ST^12345||555-1234|||F|NON|54321|123-45-6789
"""
        inputs = {'hl7_message': minimal_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should parse successfully but with empty segments
        self.assertEqual(result['patient_id'], '54321')
        self.assertEqual(len(result['diagnoses']), 0)
        self.assertEqual(len(result['observations']), 0)
        self.assertEqual(len(result['procedures']), 0)
        self.assertEqual(result['visit_info'], {})

    def test_fallback_parsing_obx_segments(self):
        """Test fallback parsing specifically for OBX segments."""
        # Create a message that might fail primary parsing but work with fallback
        with patch('crew.hl7_parser.parse_message') as mock_parse:
            mock_parse.side_effect = Exception("Simulated parsing failure")
            
            inputs = {'hl7_message': SAMPLE_MESSAGES['chest_pain']}
            result = self.sim_crew.prepare_simulation(inputs)
            
            # Should have fallback-parsed observations
            self.assertIn('observations', result)
            self.assertGreater(len(result['observations']), 0)
            
            # Verify heart rate observation from fallback
            heart_rate_found = False
            for obs in result['observations']:
                if '8867-4' in obs.get('observation_identifier', ''):
                    heart_rate_found = True
                    self.assertEqual(obs['observation_value'], '88')
                    self.assertEqual(obs['units'], '/min')
                    break
            self.assertTrue(heart_rate_found, "Heart rate not found in fallback parsing")

    def test_fallback_parsing_procedures(self):
        """Test fallback parsing for procedure segments."""
        with patch('crew.hl7_parser.parse_message') as mock_parse:
            mock_parse.side_effect = Exception("Simulated parsing failure")
            
            inputs = {'hl7_message': SAMPLE_MESSAGES['surgical']}
            result = self.sim_crew.prepare_simulation(inputs)
            
            # Should have fallback-parsed procedures
            self.assertIn('procedures', result)
            self.assertGreater(len(result['procedures']), 0)
            
            procedure = result['procedures'][0]
            self.assertEqual(procedure['procedure_code'], '81.51')
            self.assertIn('TOTAL HIP REPLACEMENT', procedure['procedure_description'])

    def test_edge_case_empty_fields(self):
        """Test handling of HL7 messages with empty fields."""
        message_with_empty_fields = """
MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|99999|99999^^^SIMULATOR^MR||||||||||||||||
DG1|1||R00.0||20240101120000|A
OBX|1|NM|||95||95-100|N|||F
"""
        inputs = {'hl7_message': message_with_empty_fields}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle empty fields gracefully
        self.assertEqual(result['patient_id'], '99999')
        self.assertGreater(len(result['diagnoses']), 0)
        self.assertGreater(len(result['observations']), 0)
        
        # Verify empty fields are handled
        diagnosis = result['diagnoses'][0]
        self.assertEqual(diagnosis['coding_system'], '')
        self.assertEqual(diagnosis['description'], '')

    def test_validation_statistics(self):
        """Test validation statistics reporting."""
        inputs = {'hl7_message': SAMPLE_MESSAGES['chest_pain']}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should have validation statistics
        self.assertIn('parsing_success', result)
        self.assertIn('validation_warnings', result)
        self.assertIn('validation_errors_count', result)
        
        # For a valid message, should have successful parsing
        self.assertTrue(result['parsing_success'])
        self.assertIsInstance(result['validation_warnings'], int)
        self.assertIsInstance(result['validation_errors_count'], int)

if __name__ == '__main__':
    unittest.main()