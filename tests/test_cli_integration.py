import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import os
import sys
from io import StringIO
import simulate
from sample_data.sample_messages import SAMPLE_MESSAGES


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the CLI functionality."""

    def setUp(self):
        """Set up test environment with proper mocking."""
        # Patch sys.argv to avoid conflicts with test runner
        self.argv_patcher = patch.object(sys, 'argv', ['simulate.py'])
        self.argv_patcher.start()
        
    def tearDown(self):
        """Clean up patches."""
        self.argv_patcher.stop()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    @patch('simulate.HealthcareSimulationCrew')
    def test_cli_with_scenario_argument(self, mock_crew_class):
        """Test CLI with scenario argument."""
        # Setup mock crew
        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "Mock simulation result for chest pain scenario"
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []
        mock_crew_class.return_value = mock_crew_instance
        
        # Test with scenario argument
        with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain']):
            with patch('builtins.print') as mock_print:
                try:
                    simulate.main()
                except SystemExit:
                    pass  # Expected for successful execution
                
                # Verify crew was initialized and executed
                mock_crew_class.assert_called_once()
                mock_crew_instance.crew().kickoff.assert_called_once()
                
                # Verify output was printed
                mock_print.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    @patch('simulate.HealthcareSimulationCrew')
    def test_cli_with_input_file(self, mock_crew_class):
        """Test CLI with input file argument."""
        # Setup mock crew  
        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "Mock simulation result from file"
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []
        mock_crew_class.return_value = mock_crew_instance
        
        # Create temporary file with HL7 data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hl7') as temp_file:
            temp_file.write(SAMPLE_MESSAGES['chest_pain'])
            temp_file_path = temp_file.name
        
        try:
            with patch.object(sys, 'argv', ['simulate.py', '--input', temp_file_path]):
                with patch('builtins.print') as mock_print:
                    try:
                        simulate.main()
                    except SystemExit:
                        pass  # Expected for successful execution
                    
                    # Verify crew was initialized and executed
                    mock_crew_class.assert_called_once()
                    mock_crew_instance.crew().kickoff.assert_called_once()
                    
                    # Verify output was printed
                    mock_print.assert_called()
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    @patch('simulate.HealthcareSimulationCrew')
    def test_cli_with_output_file(self, mock_crew_class):
        """Test CLI with output file argument."""
        # Setup mock crew
        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "Mock simulation result for output file test"
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_instance.patient_data = {}
        mock_crew_instance.validation_issues = []
        mock_crew_class.return_value = mock_crew_instance
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            output_file_path = temp_file.name
        
        try:
            with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain', '--output', output_file_path]):
                try:
                    simulate.main()
                except SystemExit:
                    pass  # Expected for successful execution
                
                # Verify crew was executed
                mock_crew_class.assert_called_once()
                mock_crew_instance.crew().kickoff.assert_called_once()
                
                # Verify output file was created and contains expected content
                self.assertTrue(os.path.exists(output_file_path))
                with open(output_file_path, 'r') as f:
                    content = f.read()
                    self.assertIn("SYNTHETIC CARE PATHWAY SIMULATION RESULTS", content)
                    self.assertIn("Mock simulation result for output file test", content)
        finally:
            # Clean up temporary file
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    @patch.dict(os.environ, {}, clear=True)  # Remove all environment variables
    def test_cli_no_api_key_error(self):
        """Test CLI behavior when no API key is provided."""
        with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain']):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    simulate.main()
                
                # Verify error message was printed
                mock_print.assert_called()
                error_printed = any("API key" in str(call) for call in mock_print.call_args_list)
                self.assertTrue(error_printed)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_cli_invalid_scenario(self):
        """Test CLI with invalid scenario name."""
        with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'invalid_scenario']):
            with patch('builtins.print') as mock_print:
                try:
                    simulate.main()
                except SystemExit:
                    pass  # Expected for error case
                
                # Should fall back to default scenario or show available scenarios
                mock_print.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_cli_verbose_mode(self):
        """Test CLI verbose mode."""
        with patch('simulate.HealthcareSimulationCrew') as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.raw = "Verbose simulation result"
            mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
            mock_crew_instance.patient_data = {}
            mock_crew_instance.validation_issues = []
            mock_crew_class.return_value = mock_crew_instance
            
            with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain', '--verbose']):
                with patch('builtins.print') as mock_print:
                    try:
                        simulate.main()
                    except SystemExit:
                        pass
                    
                    # Verbose mode should produce additional output
                    mock_print.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_cli_different_backends(self):
        """Test CLI with different LLM backends."""
        backends_to_test = ['openai', 'ollama', 'openrouter']
        
        for backend in backends_to_test:
            with self.subTest(backend=backend):
                with patch('simulate.HealthcareSimulationCrew') as mock_crew_class:
                    mock_crew_instance = MagicMock()
                    mock_result = MagicMock()
                    mock_result.raw = f"Result from {backend} backend"
                    mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
                    mock_crew_instance.patient_data = {}
                    mock_crew_instance.validation_issues = []
                    mock_crew_class.return_value = mock_crew_instance
                    
                    argv = ['simulate.py', '--scenario', 'chest_pain', '--backend', backend]
                    if backend == 'ollama':
                        argv.extend(['--model', 'llama2'])
                    elif backend == 'openrouter':
                        argv.extend(['--model', 'anthropic/claude-3-haiku:beta'])
                    
                    with patch.object(sys, 'argv', argv):
                        try:
                            simulate.main()
                        except SystemExit:
                            pass
                        
                        # Verify crew was created (indicating backend was handled)
                        mock_crew_class.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_cli_temperature_parameter(self):
        """Test CLI with temperature parameter."""
        with patch('simulate.HealthcareSimulationCrew') as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.raw = "Result with custom temperature"
            mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
            mock_crew_instance.patient_data = {}
            mock_crew_instance.validation_issues = []
            mock_crew_class.return_value = mock_crew_instance
            
            with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain', '--temperature', '0.5']):
                try:
                    simulate.main()
                except SystemExit:
                    pass
                
                # Verify crew was created with custom config
                mock_crew_class.assert_called_once()

    def test_format_result_function(self):
        """Test the format_result utility function."""
        mock_result = MagicMock()
        mock_result.raw = "Test simulation output"
        
        # Test without output file
        formatted = simulate.format_result(mock_result)
        self.assertIn("SYNTHETIC CARE PATHWAY SIMULATION RESULTS", formatted)
        self.assertIn("Test simulation output", formatted)
        self.assertIn("Timestamp:", formatted)
        
        # Test with output file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            output_file_path = temp_file.name
        
        try:
            formatted = simulate.format_result(mock_result, output_file_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(output_file_path))
            
            # Verify file content
            with open(output_file_path, 'r') as f:
                file_content = f.read()
                self.assertIn("SYNTHETIC CARE PATHWAY SIMULATION RESULTS", file_content)
                self.assertIn("Test simulation output", file_content)
        finally:
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_all_sample_scenarios(self):
        """Test CLI with all available sample scenarios."""
        from sample_data.sample_messages import list_scenarios
        
        scenarios = list_scenarios()
        self.assertGreater(len(scenarios), 0, "Should have sample scenarios available")
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                with patch('simulate.HealthcareSimulationCrew') as mock_crew_class:
                    mock_crew_instance = MagicMock()
                    mock_result = MagicMock()
                    mock_result.raw = f"Result for {scenario} scenario"
                    mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
                    mock_crew_instance.patient_data = {}
                    mock_crew_instance.validation_issues = []
                    mock_crew_class.return_value = mock_crew_instance
                    
                    with patch.object(sys, 'argv', ['simulate.py', '--scenario', scenario]):
                        try:
                            simulate.main()
                        except SystemExit:
                            pass
                        
                        # Each scenario should result in crew execution
                        mock_crew_class.assert_called_once()
                        mock_crew_instance.crew().kickoff.assert_called_once()


class TestCLIErrorHandling(unittest.TestCase):
    """Test error handling in CLI functionality."""

    def setUp(self):
        """Set up test environment."""
        self.argv_patcher = patch.object(sys, 'argv', ['simulate.py'])
        self.argv_patcher.start()
        
    def tearDown(self):
        """Clean up patches."""
        self.argv_patcher.stop()

    def test_nonexistent_input_file(self):
        """Test CLI with nonexistent input file."""
        nonexistent_file = "/tmp/nonexistent_file.hl7"
        
        with patch.object(sys, 'argv', ['simulate.py', '--input', nonexistent_file]):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    simulate.main()
                
                # Should print error about file not found
                mock_print.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_invalid_temperature_value(self):
        """Test CLI with invalid temperature value."""
        with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain', '--temperature', 'invalid']):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    simulate.main()
                
                # Should handle argument parsing error
                mock_print.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
    def test_permission_denied_output_file(self):
        """Test CLI with output file in protected directory."""
        protected_path = "/root/protected_output.txt"  # Assuming this will fail
        
        with patch('simulate.HealthcareSimulationCrew') as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.raw = "Test output"
            mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
            mock_crew_instance.patient_data = {}
            mock_crew_instance.validation_issues = []
            mock_crew_class.return_value = mock_crew_instance
            
            with patch.object(sys, 'argv', ['simulate.py', '--scenario', 'chest_pain', '--output', protected_path]):
                with patch('builtins.print') as mock_print:
                    try:
                        simulate.main()
                    except (SystemExit, PermissionError):
                        pass  # Either is acceptable
                    
                    # Crew should still execute even if file write fails
                    mock_crew_class.assert_called_once()


if __name__ == '__main__':
    unittest.main()