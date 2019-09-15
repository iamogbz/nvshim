# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["TestParseArgs.test_accepts_any_arg_for_bin_file 1"] = (
    GenericRepr("Namespace(bin_args=[], bin_file='npm')"),
    ["--version", "--help"],
)

snapshots["TestParseArgs.test_accepts_bin_file_arg 1"] = (
    GenericRepr("Namespace(bin_args=[], bin_file='node')"),
    [],
)

snapshots[
    "TestMain.test_fails_when_nvm_dir_not_available[true] 1"
] = """Executing shim version 0.0.0
Environment variable 'NVM_DIR' missing"""

snapshots[
    "TestMain.test_fails_when_nvm_dir_not_available[false] 1"
] = "Environment variable 'NVM_DIR' missing"
