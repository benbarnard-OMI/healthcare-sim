import unittest
from unittest.mock import patch, MagicMock, call
import argparse
import os
import sys
import simulate
from simulate import main as simulate_main
from sample_data.sample_messages import SAMPLE_MESSAGES


class TestSimulate(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        # Patch sys.argv to avoid conflicts with test runner
        self.original_argv = sys.argv[:]
    
    def tearDown(self):
        """Clean up test environment."""
        sys.argv = self.original_argv

    @patch('simulate.HealthcareSimulationCrew')
    @patch('simulate.get_message')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_main_with_scenario(self, mock_get_message, mock_crew):
        # Mock the sample message
        mock_get_message.return_value = SAMPLE_MESSAGES['chest_pain']
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.return_value = MagicMock(raw="Simulation result")
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []
        
        # Mock command-line arguments
        test_args = ['simulate.py', '--scenario', 'chest_pain']
        with patch('sys.argv', test_args):
            try:
                simulate.main()
            except SystemExit:
                pass  # Expected for successful execution
        
        # Check if the sample message was retrieved
        mock_get_message.assert_called_with('chest_pain')
        
        # Check if the simulation was run
        mock_crew_instance.crew().kickoff.assert_called_with(inputs={"hl7_message": SAMPLE_MESSAGES['chest_pain']})
        
    @patch('simulate.HealthcareSimulationCrew')
    @patch('simulate.open')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_main_with_input_file(self, mock_open, mock_crew):
        # Mock the input file
        mock_open.return_value.__enter__.return_value.read.return_value = SAMPLE_MESSAGES['chest_pain']
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.return_value = MagicMock(raw="Simulation result")
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []
        
        # Mock command-line arguments
        test_args = ['simulate.py', '--input', 'test_file.hl7']
        with patch('sys.argv', test_args):
            try:
                simulate.main()
            except SystemExit:
                pass  # Expected for successful execution
        
        # Check if the input file was read
        mock_open.assert_called_with('test_file.hl7', 'r')
        
        # Check if the simulation was run
        mock_crew_instance.crew().kickoff.assert_called_with(inputs={"hl7_message": SAMPLE_MESSAGES['chest_pain']})
        
    @patch.dict(os.environ, {}, clear=True)  # No API key in environment
    def test_main_no_api_key(self):
        # Mock command-line arguments
        test_args = ['simulate.py', '--scenario', 'chest_pain']
        
        # Expect sys.exit(1) to be called, which raises SystemExit
        with patch('sys.argv', test_args), self.assertRaises(SystemExit) as cm:
            simulate_main()  # Use aliased main
        
        self.assertEqual(cm.exception.code, 1)  # Check the exit code

    @patch('simulate.HealthcareSimulationCrew')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_default_scenario"})
    def test_main_uses_default_scenario_when_no_input(self, mock_crew):
        # Setup mock crew instance
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew.return_value.kickoff.return_value = MagicMock(raw="Default scenario simulation result")
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []

        # Mock command-line arguments with no scenario or input
        test_args = ['simulate.py']
        with patch('sys.argv', test_args):
            try:
                simulate_main()
            except SystemExit:
                pass  # Expected for successful execution

        # Assertions
        # 1. HealthcareSimulationCrew was initialized
        mock_crew.assert_called_once()

        # 2. kickoff was called
        mock_crew_instance.crew().kickoff.assert_called_once()

        # 3. kickoff was called with the default chest pain message
        call_args = mock_crew_instance.crew().kickoff.call_args
        self.assertIsNotNone(call_args)
        inputs = call_args.kwargs.get('inputs')
        self.assertIsNotNone(inputs)
        self.assertEqual(inputs.get('hl7_message'), SAMPLE_MESSAGES["chest_pain"])

if __name__ == '__main__':
    unittest.main()
