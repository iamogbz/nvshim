"""nvshim constants"""
from enum import IntEnum


class ErrorCode(IntEnum):
    """nvshim process exit error codes"""

    ENV_NVM_DIR_MISSING = 1003
    EXECUTABLE_NOT_FOUND = 1002
    KEYBOARD_INTERRUPT = 130
    VERSION_NOT_INSTALLED = 1001


shims = {"node", "npm", "npx"}
