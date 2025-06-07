import unittest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest
import os

# Assuming dashboard.py is in the root of the project directory.
# If your test execution context is different, you might need to adjust this path.
DASHBOARD_FILE_PATH = "dashboard.py"
# Attempt to locate dashboard.py relative to this test file if not found directly
if not os.path.exists(DASHBOARD_FILE_PATH) and "tests" in os.getcwd():
    DASHBOARD_FILE_PATH = os.path.join("..", DASHBOARD_FILE_PATH)


class TestDashboardApp(unittest.TestCase):
    def setUp(self):
        # Using patch.dict for cleaner environment variable management
        self.patch_env = patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key_from_setup"})
        self.patch_env.start()

        # Ensure the path to dashboard.py is correct
        if not os.path.exists(DASHBOARD_FILE_PATH):
            raise FileNotFoundError(
                f"dashboard.py not found. Attempted path: {os.path.abspath(DASHBOARD_FILE_PATH)}. "
                "Ensure the path is correct relative to the test execution directory."
            )
        self.at = AppTest.from_file(DASHBOARD_FILE_PATH)
        self.at.run()

    def tearDown(self):
        self.patch_env.stop()

    def test_api_key_input_exists(self):
        # Check if the API key input widget exists in the sidebar
        self.assertTrue(self.at.sidebar.text_input(label="OpenAI API Key").exists)

    def test_run_simulation_without_api_key_shows_error(self):
        # Temporarily remove the API key for this specific test using a new AppTest instance
        # This ensures a clean environment for this test case.
        with patch.dict(os.environ, {}, clear=True): # Clear all env vars, especially OPENAI_API_KEY
            at_no_key = AppTest.from_file(DASHBOARD_FILE_PATH)
            # Do not run at_no_key yet, let the button click trigger the run and error

            # Simulate clicking the run button
            # The button click itself will trigger the first run if not run before.
            at_no_key.sidebar.button(label="Run Simulation").click().run()

            # Check for an error message
            self.assertTrue(at_no_key.error.exists)
            self.assertIn("Please enter your OpenAI API key", at_no_key.error[0].value)

    def test_scenario_selection_exists_and_has_options(self):
        # Check if the scenario selection widget exists
        scenario_selector = self.at.sidebar.selectbox(label="Select Patient Scenario")
        self.assertTrue(scenario_selector.exists)
        # Check if it has options. This relies on list_scenarios() from sample_messages.py
        # For a unit test, one might mock list_scenarios, but for AppTest, we test the integration.
        from sample_data.sample_messages import list_scenarios # Assuming this can be imported
        self.assertGreater(len(scenario_selector.options), 0)
        self.assertIsNotNone(scenario_selector.value) # It should have a default selected value

    def test_custom_hl7_input_exists(self):
        # Check if the custom HL7 text area exists
        self.assertTrue(self.at.sidebar.text_area(label="Or enter custom HL7 message").exists)

    @patch('dashboard.HealthcareSimulationCrew') # Patch where it's looked up (dashboard.py)
    def test_run_simulation_button_click_calls_crew(self, MockHealthcareSimulationCrew):
        # Setup mock crew instance and its methods
        mock_crew_instance = MockHealthcareSimulationCrew.return_value
        mock_crew_instance.crew.return_value.kickoff.return_value = MagicMock(raw="Mocked simulation result")
        # Ensure patient_data and validation_issues are attributes of the instance
        mock_crew_instance.patient_data = {'patient_info': {'id': 'test_id', 'name': 'Test Patient', 'dob': '1990-01-01', 'gender': 'M', 'address': '123 Test St'}}
        mock_crew_instance.validation_issues = []

        # The API key is set in setUp via os.environ for the self.at instance
        # If a specific value is needed for the widget itself:
        # self.at.sidebar.text_input(label="OpenAI API Key").set_value("fake_api_key_for_test").run()
        
        # Simulate clicking the run button
        self.at.sidebar.button(label="Run Simulation").click().run()

        # Assertions
        MockHealthcareSimulationCrew.assert_called_once() # Check if crew was initialized
        mock_crew_instance.crew().kickoff.assert_called_once() # Check if kickoff was called

        # Check if results are displayed (e.g., a success message)
        self.assertTrue(self.at.success.exists)
        self.assertIn("Simulation completed successfully!", self.at.success[0].value)

        # Check if patient ID from mocked data is displayed in a metric
        patient_id_metric = self.at.metric(label="Patient ID")
        self.assertTrue(patient_id_metric.exists)
        self.assertEqual(patient_id_metric.value, "test_id")

        # Check for other patient info metrics
        name_metric = self.at.metric(label="Name")
        self.assertTrue(name_metric.exists)
        self.assertEqual(name_metric.value, "Test Patient")

        dob_metric = self.at.metric(label="DOB")
        self.assertTrue(dob_metric.exists)
        self.assertEqual(dob_metric.value, "1990-01-01")

if __name__ == '__main__':
    unittest.main()
