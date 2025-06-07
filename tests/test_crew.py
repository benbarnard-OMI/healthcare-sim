import unittest
from unittest.mock import patch
from crew import HealthcareSimulationCrew, UNKNOWN_PATIENT_ID
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
        self.assertEqual(result['patient_id'], UNKNOWN_PATIENT_ID) # Use the constant
        self.assertIn('validation_errors', result)
        self.assertGreater(len(result['validation_errors']), 0)
        # Check specific error details if possible/needed
        self.assertTrue(any(issue['error_type'] for issue in result['validation_errors']))

    def test_prepare_simulation_hl7_missing_dg1(self):
        # HL7 message without DG1 segment
        hl7_message_no_dg1 = (
            "MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1\n"
            "PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789\n"
            "PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000"
        )
        inputs = {"hl7_message": hl7_message_no_dg1}
        prepared_inputs = self.sim_crew.prepare_simulation(inputs)
        self.assertEqual(prepared_inputs['patient_id'], "12345")
        self.assertIn('patient_info', prepared_inputs)
        self.assertEqual(prepared_inputs['diagnoses'], []) # Expect empty diagnoses list
        self.assertTrue(len(self.sim_crew.validation_issues) == 0) # Expect no validation issues for this specific case

    def test_prepare_simulation_hl7_missing_address(self):
        # HL7 message with PID segment missing patient address (field 11)
        hl7_message_no_address = (
            "MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1\n"
            "PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|DOE^JANE^F||19800120|F|||||555-555-1212|||F|NON|67890|987-65-4321\n"
            "PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000\n"
            "DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A"
        )
        inputs = {"hl7_message": hl7_message_no_address}
        prepared_inputs = self.sim_crew.prepare_simulation(inputs)
        self.assertEqual(prepared_inputs['patient_id'], "12345")
        self.assertIn('patient_info', prepared_inputs)
        self.assertEqual(prepared_inputs['patient_info']['address'], "Unknown") # Check default value
        self.assertTrue(len(self.sim_crew.validation_issues) == 0)

    @patch('crew.hl7_parser.parse_message')
    def test_prepare_simulation_fallback_varied_pid(self, mock_parse_message):
        mock_parse_message.side_effect = Exception("Simulated parsing failure")
        # PID with extra pipe, but ID still in 3rd component of 4th field (index 3)
        hl7_message_varied_pid = (
            "MSH|^~\&|OTHER_SYS|OTHER_FAC|||20240505220000||ADT^A01|MSGID002|P|2.5.1\n"
            "PID|1||PATID789^^^SOURCE^MR||SMITH^JOHN||19700101|M|||||||||||SSN1234"
        )
        inputs = {"hl7_message": hl7_message_varied_pid}
        prepared_inputs = self.sim_crew.prepare_simulation(inputs)

        self.assertEqual(prepared_inputs['patient_id'], "PATID789")
        self.assertTrue(any(issue['message'] == "Simulated parsing failure" for issue in self.sim_crew.validation_issues))

    @patch('crew.hl7_parser.parse_message')
    def test_prepare_simulation_fallback_failure_graceful(self, mock_parse_message):
        mock_parse_message.side_effect = Exception("Simulated primary parsing failure")
        # Malformed PID that the fallback will also fail to parse (e.g., no clear ID in expected fallback spot)
        hl7_message_bad_pid_fallback = (
            "MSH|^~\&|SYS|FAC|||202301011000||ADT^A01|MSG003|P|2.5.1\n"
            "PID|1||||||||||||||||||" # Empty PID fields
        )
        inputs = {"hl7_message": hl7_message_bad_pid_fallback}
        prepared_inputs = self.sim_crew.prepare_simulation(inputs)

        self.assertEqual(prepared_inputs['patient_id'], UNKNOWN_PATIENT_ID)
        # Check that the primary parsing failure was logged
        self.assertTrue(any(issue['details'] == "Simulated primary parsing failure" and issue['error_type'] == 'Exception' for issue in self.sim_crew.validation_issues))
        # Check that the fallback parsing error was logged
        self.assertTrue(any(issue['error_type'] == "FallbackParsingError" for issue in self.sim_crew.validation_issues), "FallbackParsingError issue not found")


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
