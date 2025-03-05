import unittest
from crew import HealthcareSimulationCrew
from sample_data.sample_messages import SAMPLE_MESSAGES

class TestHealthcareSimulationCrew(unittest.TestCase):

    def setUp(self):
        self.sim_crew = HealthcareSimulationCrew()

    def test_prepare_simulation_valid_message(self):
        inputs = {'hl7_message': SAMPLE_MESSAGES['chest_pain']}
        result = self.sim_crew.prepare_simulation(inputs)
        self.assertIn('patient_id', result)
        self.assertIn('patient_info', result)
        self.assertIn('diagnoses', result)
        self.assertIn('full_message', result)
        self.assertEqual(result['patient_id'], '12345')
        self.assertEqual(result['patient_info']['name'], 'SMITH^JOHN^M')

    def test_prepare_simulation_invalid_message(self):
        inputs = {'hl7_message': 'INVALID MESSAGE'}
        result = self.sim_crew.prepare_simulation(inputs)
        self.assertIn('patient_id', result)
        self.assertEqual(result['patient_id'], 'UNKNOWN')
        self.assertIn('validation_errors', result)
        self.assertGreater(len(result['validation_errors']), 0)

    def test_data_ingestion_agent(self):
        agent = self.sim_crew.data_ingestion_agent()
        self.assertEqual(agent.config['role'], 'HL7 Data Ingestion Specialist')

    def test_diagnostics_agent(self):
        agent = self.sim_crew.diagnostics_agent()
        self.assertEqual(agent.config['role'], 'Clinical Diagnostics Analyst')

    def test_treatment_planner(self):
        agent = self.sim_crew.treatment_planner()
        self.assertEqual(agent.config['role'], 'Treatment Planning Specialist')

    def test_care_coordinator(self):
        agent = self.sim_crew.care_coordinator()
        self.assertEqual(agent.config['role'], 'Patient Care Coordinator')

    def test_outcome_evaluator(self):
        agent = self.sim_crew.outcome_evaluator()
        self.assertEqual(agent.config['role'], 'Clinical Outcomes Analyst')

    def test_ingest_hl7_data_task(self):
        task = self.sim_crew.ingest_hl7_data()
        self.assertEqual(task.config['description'], 'Parse and validate the incoming Synthea HL7 message for patient {patient_id}.')

    def test_analyze_diagnostics_task(self):
        task = self.sim_crew.analyze_diagnostics()
        self.assertEqual(task.config['description'], 'Analyze the structured patient data to identify probable diagnoses and risk factors.')

    def test_create_treatment_plan_task(self):
        task = self.sim_crew.create_treatment_plan()
        self.assertEqual(task.config['description'], 'Develop a comprehensive treatment plan based on diagnostic findings.')

    def test_coordinate_care_task(self):
        task = self.sim_crew.coordinate_care()
        self.assertEqual(task.config['description'], 'Manage the overall patient care workflow.')

    def test_evaluate_outcomes_task(self):
        task = self.sim_crew.evaluate_outcomes()
        self.assertEqual(task.config['description'], 'Monitor and analyze treatment outcomes for the patient.')

    def test_crew(self):
        crew = self.sim_crew.crew()
        self.assertEqual(len(crew.agents), 5)
        self.assertEqual(len(crew.tasks), 5)
        self.assertEqual(crew.process, 'hierarchical')
        self.assertEqual(crew.manager_agent.config['role'], 'Patient Care Coordinator')

if __name__ == '__main__':
    unittest.main()
