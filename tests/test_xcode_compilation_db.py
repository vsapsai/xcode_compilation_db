#!/usr/bin/env python

# Actually, it is not a unit test, but integration test.

import json
import os
import subprocess
import unittest

DB_FILENAME = "compile_commands.json"

def first_different_character_index(str1, str2):
    """Returns index of the first character which differs in str1 and str2."""
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return i
    if len(str1) != len(str2):
        return min_length
    return -1


class CompilationDatabaseRegressionTestCase(unittest.TestCase):
    def test(self):
        test_directory = os.path.dirname(os.path.abspath(__file__))
        test_project_directory = os.path.join(test_directory, "TestProject")
        command_directory = os.path.dirname(test_directory)
        command_path = os.path.join(command_directory, "xcode_compilation_db.py")
        self.create_compilation_database(test_project_directory, command_path)
        # Compare actual and expected compilation databases.
        expected_compilation_db = None
        with open(os.path.join(test_project_directory, "compile_commands_expected.json"), "rt") as f:
            expected_compilation_db = json.load(f)
        actual_compilation_db = None
        with open(os.path.join(test_project_directory, DB_FILENAME), "rt") as f:
            actual_compilation_db = json.load(f)
        self.assert_equal_compilation_db(expected_compilation_db, actual_compilation_db, test_project_directory)

    def create_compilation_database(self, project_directory, command_path):
        db_path = os.path.join(project_directory, DB_FILENAME)
        if os.path.exists(db_path):
            os.remove(db_path)
        os.chdir(project_directory)
        subprocess.check_call(["xcodebuild", "-scheme", "TestProject", "clean"])
        command = [command_path, "xcodebuild", "-scheme", "TestProject", "build"]
        subprocess.check_call(command)

    def assert_equal_compilation_db(self, expected_db, actual_db, project_directory):
        self.assertEqual(len(expected_db), len(actual_db), "Length should be the same")
        actual_db_dict = {record["file"]: record for record in actual_db}
        random_dir_part = None
        assert len(actual_db_dict) == len(actual_db), "Expect no file duplicates"
        for expected_record in expected_db:
            actual_record = actual_db_dict[expected_record["file"]]
            self.assertEqual(set(expected_record.keys()), set(actual_record.keys()), "Keys should be equal")
            for key, value in expected_record.iteritems():
                value = value.replace("{{PROJECT_DIR}}", project_directory)
                if key == "command":
                    if random_dir_part is None:
                        random_dir_part = self.detect_random_dir_part(value, actual_record[key])
                        self.assertIsNotNone(random_dir_part, "Failed to detect random directory part")
                    value = value.replace("{{RANDOM_DIR_PART}}", random_dir_part)
                self.assertEqual(value, actual_record[key])

    def detect_random_dir_part(self, expected_str, actual_str):
        different_char_i = first_different_character_index(expected_str, actual_str)
        if different_char_i == -1:
            return None
        if not expected_str[different_char_i:].startswith("{{RANDOM_DIR_PART}}"):
            return None
        random_part = actual_str[different_char_i : different_char_i+28]
        return random_part

if __name__ == "__main__":
    unittest.main()
