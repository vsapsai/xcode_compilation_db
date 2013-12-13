#!/usr/bin/env python

import contextlib
import fcntl
import json
import os
import shlex
import subprocess
import sys

C_COMPILER_KEY = "CC"
CPP_COMPILER_KEY = "CXX"
C_LINKER_KEY = "LD"
CPP_LINKER_KEY = "LDPLUSPLUS"
CLANG_PATH_KEY = "COMPILATION_DB_CLANG_PATH"
DB_FILENAME = "compile_commands.json"
DB_PATH_KEY = "COMPILATION_DB_DATABASE_PATH"

JSON_INDENT = 2

# Used by compiler interposers.

try:
    shell_quote = shlex.quote
except AttributeError:
    import pipes
    shell_quote = pipes.quote

def process_command(argv, is_cpp=False):
    clang_path = os.environ[CLANG_PATH_KEY]
    if is_cpp:
        clang_path += "++"
    argv[0] = clang_path
    save_compiler_command(argv)
    return subprocess.call(argv)

def save_compiler_command(argv):
    record = compiler_command_to_db_record(argv)
    if record is None:
        return
    compilation_db_path = os.environ[DB_PATH_KEY]
    with open(compilation_db_path, "r+t") as db_file:
        # Lock file because Xcode compiles multiple files at once.
        with lock_file(db_file):
            db = json.load(db_file)
            db.append(record)
            # Rewrite file content.
            db_file.seek(0)
            db_file.truncate(0)
            json.dump(db, db_file, indent=JSON_INDENT)
            # Write file to disk.
            db_file.flush()
            os.fsync(db_file.fileno())

def compiler_command_to_db_record(argv):
    """Create dictionary suitable for compile_commands.json from command-line arguments.

    Returns None if isn't compiling an existing file."""
    # Prepare directory.
    current_directory = os.getcwd()

    # Prepare file.
    # vsapsai: I rely on Xcode using -c option to find out compiled file.
    file_path = None
    for i in range(len(argv)):
        if argv[i] == "-c":
            assert i + 1 < len(argv), "-c shouldn't be the last option"
            file_path = argv[i + 1]
            break
    assert file_path is not None, "Failed to find out compiled file."
    file_path = os.path.normpath(file_path)
    if file_path == "/dev/null":
        return None
    # Relative paths are preferred.  But only when file is within working directory.
    if os.path.isabs(file_path) and file_path.startswith(current_directory):
        file_path = os.path.relpath(file_path, current_directory)

    # Prepare command.
    quoted_argv = [shell_quote(arg) for arg in argv]
    command = " ".join(quoted_argv)
    assert argv == shlex.split(command), "Shell quoting doesn't round trip"

    record = {
        "directory": current_directory,
        "command": command,
        "file": file_path
    }
    return record

@contextlib.contextmanager
def lock_file(file_object):
    try:
        fcntl.flock(file_object.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(file_object.fileno(), fcntl.LOCK_UN)

# Used by xcodebuild launcher

def init_db_storage():
    """Creates and returns path to empty compilation database.

    Terminates script if database already exists."""
    working_directory = os.getcwd()
    compilation_db_path = os.path.join(working_directory, DB_FILENAME)
    if os.path.lexists(compilation_db_path):
        sys.exit("{filename} already exists.".format(filename=DB_FILENAME))
    initial_db = []
    with open(compilation_db_path, "wt") as db_file:
        json.dump(initial_db, db_file, indent=JSON_INDENT)
    return compilation_db_path

def setup_environment(db_path):
    """Setup environment so that xcodebuild uses bogus compilers."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ[C_COMPILER_KEY] = os.path.join(script_dir, "c_interposer.py")
    os.environ[CPP_COMPILER_KEY] = os.path.join(script_dir, "cpp_interposer.py")
    os.environ[DB_PATH_KEY] = db_path
    clang_path = subprocess.check_output(
        ["xcrun", "-toolchain", "XcodeDefault", "-find", "clang"])
    clang_path = clang_path.strip("\n")
    os.environ[CLANG_PATH_KEY] = clang_path
    # When 'CC' is set, xcodebuild uses it to do all linking.  Linking commands
    # aren't needed for compile_commands.json, so return back correct linkers.
    os.environ[C_LINKER_KEY] = clang_path
    os.environ[CPP_LINKER_KEY] = clang_path + "++"

def main():
    db_path = init_db_storage()
    setup_environment(db_path)
    assert sys.argv[1] == "xcodebuild"
    subprocess.call(sys.argv[1:])

if __name__ == "__main__":
    main()
