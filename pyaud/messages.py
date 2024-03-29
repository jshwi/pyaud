"""
pyaud.messages
==============
"""

AUDIT_PASSED = "Success: all checks have passed"
AUDIT_FAILED = "Failed: one or more checks have failed"
AUDIT_RUNNING = "running the following plugins"
TYPE_ERROR = "can only register one of the following: {valid}; not {invalid}"
FAILED = "Failed: returned non-zero exit status {returncode}"
NAME_CONFLICT_ERROR = "plugin name conflict at {plugin}: '{name}'"
NOT_FOUND = "no plugin named `{name}` found"
NO_FILES_CHANGED = "No changes have been made to audited files"
NO_FILE_CHANGED = "No changes have been made to audited file"
SUCCESS_FILE = "Success: no issues found in file"
SUCCESS_FILES = "Success: no issues found in {len} source files"
REMOVED_FILES = "Failed: removed files might not be staged"
RUN_COMMAND = "try running {command}"
