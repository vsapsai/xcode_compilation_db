#!/usr/bin/env python

# Actually, it is not a unit test, but integration test.

import json
import os
import subprocess
import unittest

DB_FILENAME = "compile_commands.json"

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
        assert len(actual_db_dict) == len(actual_db), "Expect no file duplicates"
        for expected_record in expected_db:
            actual_record = actual_db_dict[expected_record["file"]]
            self.assertEqual(set(expected_record.keys()), set(actual_record.keys()), "Keys should be equal")
            for key, value in expected_record.iteritems():
                value = value.replace("{{PROJECT_DIR}}", project_directory)
                self.assertEqual(value, actual_record[key])

if __name__ == "__main__":
    unittest.main()
