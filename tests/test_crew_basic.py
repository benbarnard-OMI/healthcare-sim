import unittest
from unittest.mock import patch, MagicMock
import os


class TestHealthcareSimulationCrewBasic(unittest.TestCase):
    """Basic tests for crew functionality without full initialization."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_import_crew_module(self):
        """Test that crew module can be imported."""
        from crew import HealthcareSimulationCrew, UNKNOWN_PATIENT_ID
        self.assertEqual(UNKNOWN_PATIENT_ID, "UNKNOWN_PATIENT_ID")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})  
    def test_prepare_simulation_basic(self):
        """Test basic HL7 message preparation without full crew setup."""
        from crew import HealthcareSimulationCrew
        from sample_data.sample_messages import SAMPLE_MESSAGES
        
        # Create instance without triggering CrewAI initialization
        with patch.object(HealthcareSimulationCrew, '__init__', lambda x: None):
            sim_crew = HealthcareSimulationCrew()
            # Manually set required attributes
            sim_crew.patient_data = {}
            sim_crew.validation_issues = []
            
            # Test the prepare_simulation method directly
            inputs = {'hl7_message': SAMPLE_MESSAGES['chest_pain']}
            
            # Mock the hl7 parsing to avoid complex dependencies
            with patch('crew.hl7_parser.parse_message') as mock_parse:
                mock_message = MagicMock()
                mock_message.PID.PID_3[0][0][0].value = "12345"  # Patient ID
                mock_message.PID.PID_5[0][0].value = "SMITH"    # Last name
                mock_message.PID.PID_5[0][1].value = "JOHN"     # First name
                mock_message.PID.PID_5[0][2].value = "M"        # Middle name
                mock_message.PID.PID_7[0].value = "19650312"    # DOB
                mock_message.PID.PID_8[0].value = "M"           # Gender
                mock_message.PID.PID_11[0][0].value = "123 MAIN ST"  # Address
                mock_message.DG1 = []  # No diagnoses for this test
                
                mock_parse.return_value = mock_message
                
                result = sim_crew.prepare_simulation(inputs)
                
                self.assertIn('patient_id', result)
                self.assertEqual(result['patient_id'], '12345')
                self.assertIn('patient_info', result)
                self.assertEqual(result['patient_info']['name'], 'SMITH^JOHN^M')


if __name__ == '__main__':
    unittest.main()