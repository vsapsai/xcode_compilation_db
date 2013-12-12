#!/usr/bin/env python

from xcode_compilation_db import process_command
import sys

if __name__ == "__main__":
    process_command(sys.argv, is_cpp=True)
