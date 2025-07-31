import unittest
from unittest.mock import patch, MagicMock
import os
from crew import HealthcareSimulationCrew, UNKNOWN_PATIENT_ID
from tests.test_utils import create_mock_llm_config, mock_env_with_api_key


class TestHL7ParsingEdgeCases(unittest.TestCase):
    """Test HL7 parsing edge cases and error handling."""

    def setUp(self):
        """Set up test environment with mocked LLM config."""
        with mock_env_with_api_key():
            self.sim_crew = HealthcareSimulationCrew(llm_config=create_mock_llm_config())

    def test_completely_malformed_hl7(self):
        """Test handling of completely malformed HL7 messages."""
        malformed_messages = [
            "This is not HL7 at all",
            "MSH||||",  # Too few fields
            "INVALID|HEADER|FORMAT",
            "",  # Empty message
            "MSH\nPID\nDG1",  # No field separators
            "MSH|^~\\&||||||||||\nGARBAGE_SEGMENT|DATA"
        ]
        
        for message in malformed_messages:
            with self.subTest(message=message[:20] + "..." if len(message) > 20 else message):
                inputs = {'hl7_message': message}
                result = self.sim_crew.prepare_simulation(inputs)
                
                # Should handle gracefully and return unknown patient
                self.assertEqual(result['patient_id'], UNKNOWN_PATIENT_ID)
                self.assertIn('validation_errors', result)
                self.assertGreater(len(result['validation_errors']), 0)

    def test_missing_required_segments(self):
        """Test handling of messages missing required segments."""
        # Message with only MSH segment
        msh_only = "MSH|^~\\&|SYSTEM|FACILITY|RECEIVER|APP|20240101120000||ADT^A01|123|P|2.5.1"
        
        inputs = {'hl7_message': msh_only}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle missing PID gracefully
        self.assertEqual(result['patient_id'], UNKNOWN_PATIENT_ID)
        self.assertIn('validation_errors', result)

    def test_corrupted_patient_segments(self):
        """Test handling of corrupted patient segments."""
        corrupted_messages = [
            # PID with missing patient ID
            """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1||||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345""",
            
            # PID with malformed patient ID
            """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|INVALID_ID_FORMAT|INVALID_ID_FORMAT||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345""",
            
            # PID with missing name
            """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||||19700101|M|||123 MAIN ST^^CITY^ST^12345""",
            
            # PID with malformed date
            """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||INVALID_DATE|M|||123 MAIN ST^^CITY^ST^12345"""
        ]
        
        for i, message in enumerate(corrupted_messages):
            with self.subTest(case=f"corrupted_case_{i}"):
                inputs = {'hl7_message': message}
                result = self.sim_crew.prepare_simulation(inputs)
                
                # Should handle corruption gracefully
                self.assertIn('patient_id', result)
                self.assertIn('patient_info', result)
                
                # May or may not have validation errors depending on severity
                if 'validation_errors' in result:
                    self.assertIsInstance(result['validation_errors'], list)

    def test_unusual_segment_orders(self):
        """Test handling of segments in unusual orders."""
        # DG1 before PID
        unusual_order = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
DG1|1|ICD-10-CM|R07.9|CHEST PAIN|20240101120000|A
PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345
PV1|1|I|WARD^101^01||||DOC123^PHYSICIAN^JANE||||||ADM|A0|||||||||||||||||||||||||20240101120000"""
        
        inputs = {'hl7_message': unusual_order}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should still parse successfully
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)
        self.assertIn('diagnoses', result)

    def test_duplicate_segments(self):
        """Test handling of duplicate segments."""
        duplicate_pid = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345
PID|2|67890|67890^^^SYSTEM^MR||DOE^JANE||19800201|F|||456 OAK ST^^CITY^ST^12345
DG1|1|ICD-10-CM|R07.9|CHEST PAIN|20240101120000|A"""
        
        inputs = {'hl7_message': duplicate_pid}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle duplicates (typically uses first occurrence)
        self.assertIn('patient_id', result)
        self.assertIn('patient_info', result)

    def test_extremely_long_messages(self):
        """Test handling of extremely long HL7 messages."""
        # Create a message with many OBX segments
        long_message_parts = [
            "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1",
            "PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345"
        ]
        
        # Add 100 OBX segments
        for i in range(100):
            long_message_parts.append(f"OBX|{i+1}|NM|TEST{i:03d}^TEST_NAME_{i}^LN||{i}|units|0-100|N|||F")
        
        long_message = "\n".join(long_message_parts)
        
        inputs = {'hl7_message': long_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle long messages without crashing
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('observations', result)
        self.assertGreater(len(result['observations']), 0)

    def test_special_characters_in_data(self):
        """Test handling of special characters in HL7 data."""
        special_chars_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||SMITH-O'CONNOR^JOÃO^JR||19700101|M|||123 MAIN ST APT #5^^CITY^ST^12345||555-123-4567|||M|CATHOLIC|12345|123-45-6789
DG1|1|ICD-10-CM|R07.9|CHEST PAIN & SHORTNESS OF BREATH|20240101120000|A
OBX|1|ST|NOTE^CLINICAL_NOTE^LN||Patient reports "sharp pain" in chest. Says it's 8/10 severity.|||||F"""
        
        inputs = {'hl7_message': special_chars_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle special characters gracefully
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)
        self.assertIn('diagnoses', result)

    def test_encoding_issues(self):
        """Test handling of encoding issues in HL7 messages."""
        # Message with potential encoding issues
        encoding_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||MÜLLER^JOSÉ^DR||19700101|M|||STRASSE 123^^MÜNCHEN^BY^12345"""
        
        inputs = {'hl7_message': encoding_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle encoding issues gracefully
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)

    def test_empty_fields_in_required_segments(self):
        """Test handling of empty fields in required segments."""
        empty_fields_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||^^||M|||^^CITY^ST^
DG1|1||R07.9||20240101120000|A
OBX|1|||||||||||F"""
        
        inputs = {'hl7_message': empty_fields_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle empty fields gracefully
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)
        self.assertIn('validation_errors', result)
        # Should have validation warnings about missing data
        self.assertGreater(len(result['validation_errors']), 0)

    def test_unsupported_hl7_versions(self):
        """Test handling of unsupported HL7 versions."""
        unsupported_versions = [
            "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|1.0",  # Very old
            "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|3.0",  # Future version
            "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|INVALID"  # Invalid version
        ]
        
        for version_msg in unsupported_versions:
            full_message = version_msg + "\nPID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M"
            
            with self.subTest(message=version_msg[-10:]):
                inputs = {'hl7_message': full_message}
                result = self.sim_crew.prepare_simulation(inputs)
                
                # Should attempt to parse regardless of version
                self.assertIn('patient_id', result)

    def test_mixed_line_endings(self):
        """Test handling of messages with mixed line endings."""
        mixed_endings = "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1\r\nPID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M\nDG1|1|ICD-10-CM|R07.9|CHEST PAIN|20240101120000|A\r"
        
        inputs = {'hl7_message': mixed_endings}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should handle mixed line endings
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)

    def test_performance_with_large_messages(self):
        """Test performance with large HL7 messages."""
        import time
        
        # Create a large message with many segments
        large_message_parts = [
            "MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1",
            "PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345"
        ]
        
        # Add many diagnostic and observation segments
        for i in range(50):
            large_message_parts.append(f"DG1|{i+1}|ICD-10-CM|CODE{i:03d}|DIAGNOSIS_{i}|20240101120000|A")
            
        for i in range(200):
            large_message_parts.append(f"OBX|{i+1}|NM|TEST{i:03d}^TEST_NAME_{i}^LN||{i*10}|mg/dL|0-100|N|||F")
        
        large_message = "\n".join(large_message_parts)
        
        inputs = {'hl7_message': large_message}
        
        # Measure parsing time
        start_time = time.time()
        result = self.sim_crew.prepare_simulation(inputs)
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        # Should parse within reasonable time (less than 5 seconds)
        self.assertLess(parsing_time, 5.0, f"Parsing took {parsing_time:.2f} seconds, which is too long")
        
        # Should still produce valid results
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('diagnoses', result)
        self.assertIn('observations', result)
        self.assertGreater(len(result['diagnoses']), 0)
        self.assertGreater(len(result['observations']), 0)


class TestHL7ValidationIssues(unittest.TestCase):
    """Test validation issue detection and reporting."""

    def setUp(self):
        """Set up test environment."""
        with mock_env_with_api_key():
            self.sim_crew = HealthcareSimulationCrew(llm_config=create_mock_llm_config())

    def test_validation_issue_structure(self):
        """Test that validation issues have proper structure."""
        invalid_message = "INVALID_HL7_MESSAGE"
        inputs = {'hl7_message': invalid_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should have validation errors
        self.assertIn('validation_errors', result)
        validation_errors = result['validation_errors']
        self.assertIsInstance(validation_errors, list)
        
        # Each validation error should have required fields
        for error in validation_errors:
            self.assertIn('error_type', error)
            self.assertIn('message', error)
            self.assertIsInstance(error['error_type'], str)
            self.assertIsInstance(error['message'], str)

    def test_validation_warnings_vs_errors(self):
        """Test distinction between validation warnings and errors."""
        # Message with missing optional data (should generate warnings)
        warning_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||||||||12345"""
        
        inputs = {'hl7_message': warning_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        if 'validation_errors' in result and result['validation_errors']:
            # Check for different types of validation issues
            error_types = [issue['error_type'] for issue in result['validation_errors']]
            # Should distinguish between different severity levels
            self.assertTrue(any('Warning' in error_type or 'Error' in error_type for error_type in error_types))

    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        # Create message with multiple validation issues
        problematic_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||||||||||
DG1|1|||20240101120000|A
OBX|1|||||||||||F"""
        
        inputs = {'hl7_message': problematic_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should track validation statistics
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('validation_errors', result)
        
        # Validation issues should be comprehensive
        validation_errors = result['validation_errors']
        if validation_errors:
            # Should have multiple types of validation issues
            error_types = [issue['error_type'] for issue in validation_errors]
            self.assertGreater(len(set(error_types)), 0)  # At least one unique error type


class TestHL7FallbackParsing(unittest.TestCase):
    """Test fallback parsing mechanisms."""

    def setUp(self):
        """Set up test environment."""
        with mock_env_with_api_key():
            self.sim_crew = HealthcareSimulationCrew(llm_config=create_mock_llm_config())

    @patch('crew.hl7_parser.parse_message')
    def test_fallback_when_hl7apy_fails(self, mock_parse):
        """Test fallback parsing when hl7apy library fails."""
        # Make hl7apy parsing fail
        mock_parse.side_effect = Exception("HL7apy parsing failed")
        
        # Use a message that should be parseable by fallback
        fallback_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|12345|12345^^^SYSTEM^MR||SMITH^JOHN||19700101|M|||123 MAIN ST^^CITY^ST^12345
DG1|1|ICD-10-CM|R07.9|CHEST PAIN|20240101120000|A"""
        
        inputs = {'hl7_message': fallback_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Should fall back and extract patient ID
        self.assertEqual(result['patient_id'], '12345')
        self.assertIn('patient_info', result)
        
        # Should log that fallback was used
        self.assertIn('validation_errors', result)
        validation_errors = result['validation_errors']
        
        # Should have recorded the parsing failure
        primary_error_found = any(
            'HL7apy parsing failed' in issue.get('details', '') 
            for issue in validation_errors
        )
        self.assertTrue(primary_error_found, "Should record primary parsing failure")

    @patch('crew.hl7_parser.parse_message')
    def test_fallback_extraction_accuracy(self, mock_parse):
        """Test accuracy of fallback data extraction."""
        mock_parse.side_effect = Exception("Primary parsing failed")
        
        # Complex message for fallback testing
        complex_message = """MSH|^~\\&|SYSTEM|FACILITY|||20240101120000||ADT^A01|123|P|2.5.1
PID|1|PATIENT123|PATIENT123^^^SYSTEM^MR||LASTNAME^FIRSTNAME^MIDDLE||19851215|F|||456 TEST AVE^^TESTCITY^TS^54321||555-987-6543|||F|RELIGION|PATIENT123|987-65-4321
PV1|1|I|UNIT^ROOM^BED||||DOCTOR123^LASTNAME^FIRSTNAME||DEPARTMENT|||||ADM|A0|||||||||||||||||||||||||20240101120000
DG1|1|ICD-10-CM|K35.9|ACUTE APPENDICITIS|20240101120000|A
DG1|2|ICD-10-CM|Z51.11|ENCOUNTER FOR CHEMOTHERAPY|20240101120000|A
OBX|1|NM|8867-4^HEART RATE^LN||85|/min|60-100|N|||F
OBX|2|NM|8480-6^SYSTOLIC BP^LN||120|mmHg|90-130|N|||F"""
        
        inputs = {'hl7_message': complex_message}
        result = self.sim_crew.prepare_simulation(inputs)
        
        # Verify fallback extracted data correctly
        self.assertEqual(result['patient_id'], 'PATIENT123')
        
        patient_info = result['patient_info']
        self.assertIn('name', patient_info)
        self.assertIn('LASTNAME', patient_info['name'])
        self.assertIn('FIRSTNAME', patient_info['name'])
        
        # Should extract diagnoses
        diagnoses = result.get('diagnoses', [])
        self.assertGreater(len(diagnoses), 0)
        
        # Should extract observations
        observations = result.get('observations', [])
        self.assertGreater(len(observations), 0)


if __name__ == '__main__':
    unittest.main()