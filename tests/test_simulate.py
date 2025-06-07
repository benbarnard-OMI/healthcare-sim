import unittest
from unittest.mock import patch, MagicMock, call
import argparse
import os # os is used by simulate.py, good to have for context, though not directly mocked here often.
import simulate
from simulate import main as simulate_main
from sample_data.sample_messages import SAMPLE_MESSAGES

class TestSimulate(unittest.TestCase):

    @patch('simulate.HealthcareSimulationCrew')
    @patch('simulate.get_message')
    @patch('simulate.os.environ.get')
    def test_main_with_scenario(self, mock_get_env, mock_get_message, mock_crew):
        # Mock environment variable for API key
        mock_get_env.return_value = "test_api_key"
        
        # Mock the sample message
        mock_get_message.return_value = "test_hl7_message"
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.return_value = MagicMock(raw="Simulation result")
        
        # Mock command-line arguments
        test_args = ['simulate.py', '--scenario', 'chest_pain']
        with patch('sys.argv', test_args):
            simulate.main()
        
        # Check if the API key was set
        mock_get_env.assert_called_with("OPENAI_API_KEY")
        
        # Check if the sample message was retrieved
        mock_get_message.assert_called_with('chest_pain')
        
        # Check if the simulation was run
        mock_crew_instance.crew().kickoff.assert_called_with(inputs={"hl7_message": "test_hl7_message"})
        
    @patch('simulate.HealthcareSimulationCrew')
    @patch('simulate.open')
    @patch('simulate.os.environ.get')
    def test_main_with_input_file(self, mock_get_env, mock_open, mock_crew):
        # Mock environment variable for API key
        mock_get_env.return_value = "test_api_key"
        
        # Mock the input file
        mock_open.return_value.__enter__.return_value.read.return_value = "test_hl7_message"
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.return_value = MagicMock(raw="Simulation result")
        
        # Mock command-line arguments
        test_args = ['simulate.py', '--input', 'test_file.hl7']
        with patch('sys.argv', test_args):
            simulate.main()
        
        # Check if the API key was set
        mock_get_env.assert_called_with("OPENAI_API_KEY")
        
        # Check if the input file was read
        mock_open.assert_called_with('test_file.hl7', 'r')
        
        # Check if the simulation was run
        mock_crew_instance.crew().kickoff.assert_called_with(inputs={"hl7_message": "test_hl7_message"})
        
    @patch('simulate.HealthcareSimulationCrew')
    @patch('simulate.os.environ.get')
    def test_main_no_api_key(self, mock_get_env, mock_crew):
        # Mock environment variable for API key
        mock_get_env.return_value = None
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        
        # Mock command-line arguments
        test_args = ['simulate.py', '--scenario', 'chest_pain']
        # Expect sys.exit(1) to be called, which raises SystemExit
        with patch('sys.argv', test_args), self.assertRaises(SystemExit) as cm:
            simulate_main() # Use aliased main
        
        self.assertEqual(cm.exception.code, 1) # Check the exit code

        # Check if the API key was checked
        mock_get_env.assert_called_with("OPENAI_API_KEY")
        
        # Check if the simulation was not run
        mock_crew_instance.crew().kickoff.assert_not_called()

    @patch('simulate.argparse.ArgumentParser')
    @patch('simulate.os.environ.get') # This mock is for the simulate module's os.environ.get
    @patch('simulate.HealthcareSimulationCrew')
    def test_main_uses_default_scenario_when_no_input(self, MockHealthcareSimulationCrew, mock_os_environ_get_in_simulate, MockArgumentParser):
        # Mock ArgumentParser to return specific args (none for input/scenario)
        mock_args = argparse.Namespace(
            input=None,
            output=None,
            api_key="test_key_default_scenario",
            verbose=False,
            scenario=None
        )
        MockArgumentParser.return_value.parse_args.return_value = mock_args

        # Mock os.environ.get for API key (used by simulate.py if args.api_key is None)
        # In this test, args.api_key is set, so this specific mock_os_environ_get_in_simulate
        # won't be hit for the API key itself, but it's good practice if other os.environ.get calls existed.
        mock_os_environ_get_in_simulate.return_value = "test_key_default_scenario" # Default for any get call

        # Setup mock crew instance and its kickoff method
        mock_crew_instance = MockHealthcareSimulationCrew.return_value
        mock_crew_instance.crew.return_value.kickoff.return_value = MagicMock(raw="Default scenario simulation result")

        # Call the main function of simulate.py
        simulate_main()

        # Assertions
        # 1. HealthcareSimulationCrew was initialized
        MockHealthcareSimulationCrew.assert_called_once()

        # 2. kickoff was called
        mock_crew_instance.crew().kickoff.assert_called_once()

        # 3. kickoff was called with the default HL7 message
        expected_default_hl7_message = SAMPLE_MESSAGES["chest_pain"]
        actual_call_args = mock_crew_instance.crew().kickoff.call_args

        self.assertIsNotNone(actual_call_args)
        called_inputs_dict = actual_call_args.kwargs.get('inputs')
        self.assertIsNotNone(called_inputs_dict, "kickoff was not called with keyword argument 'inputs'")
        self.assertEqual(called_inputs_dict.get("hl7_message"), expected_default_hl7_message)

if __name__ == '__main__':
    unittest.main()
