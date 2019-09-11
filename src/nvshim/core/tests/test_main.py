import pytest

from ..__main__ import parse_args


class TestParseArgs:
    def test_raises_missing_bin_file(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_accepts_bin_file_arg(self, snapshot):
        snapshot.assert_match(parse_args(["node"]))

    def test_accepts_any_arg_for_bin_file(self, snapshot):
        snapshot.assert_match(parse_args(["npm", "--version", "--help"]))
