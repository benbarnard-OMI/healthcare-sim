import unittest
from unittest.mock import patch, MagicMock
import simulate

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
        with patch('sys.argv', test_args):
            simulate.main()
        
        # Check if the API key was checked
        mock_get_env.assert_called_with("OPENAI_API_KEY")
        
        # Check if the simulation was not run
        mock_crew_instance.crew().kickoff.assert_not_called()

if __name__ == '__main__':
    unittest.main()
