import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from dashboard import run_simulation, HealthcareSimulationCrew

class TestDashboard(unittest.TestCase):

    @patch('dashboard.st')
    @patch('dashboard.HealthcareSimulationCrew')
    def test_run_simulation_success(self, mock_crew, mock_st):
        # Mock the API key input
        mock_st.sidebar.text_input.return_value = "test_api_key"
        
        # Mock the HL7 message input
        mock_st.sidebar.text_area.return_value = "test_hl7_message"
        
        # Mock the selected scenario
        mock_st.sidebar.selectbox.return_value = "chest_pain"
        
        # Mock the run button click
        mock_st.sidebar.button.return_value = True
        
        # Mock the simulation crew
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.return_value = MagicMock(raw="Simulation result")
        
        # Run the simulation
        run_simulation()
        
        # Check if the API key was set
        self.assertEqual(mock_st.error.call_count, 0)
        
        # Check if the simulation result was stored in session state
        self.assertEqual(st.session_state.simulation_results.raw, "Simulation result")
        
        # Check if the success message was displayed
        mock_st.success.assert_called_with("Simulation completed successfully!")
        
    @patch('dashboard.st')
    @patch('dashboard.HealthcareSimulationCrew')
    def test_run_simulation_failure(self, mock_crew, mock_st):
        # Mock the API key input
        mock_st.sidebar.text_input.return_value = "test_api_key"
        
        # Mock the HL7 message input
        mock_st.sidebar.text_area.return_value = "test_hl7_message"
        
        # Mock the selected scenario
        mock_st.sidebar.selectbox.return_value = "chest_pain"
        
        # Mock the run button click
        mock_st.sidebar.button.return_value = True
        
        # Mock the simulation crew to raise an exception
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.crew().kickoff.side_effect = Exception("Simulation error")
        
        # Run the simulation
        run_simulation()
        
        # Check if the error message was displayed
        mock_st.error.assert_called_with("Simulation failed: Simulation error")
        
        # Check if the simulation result was not stored in session state
        self.assertIsNone(st.session_state.simulation_results)

if __name__ == '__main__':
    unittest.main()
