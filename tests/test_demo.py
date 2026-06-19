"""Unit tests for the pure helpers in demo.py.

The live REST/relay path is exercised by the manual `demo.py <fixture>` smoke run,
not here — these tests cover only the deterministic, side-effect-free helpers.
"""

import pytest

import demo


class TestParseCli:
    def test_all_expands_to_every_fixture(self):
        fixtures, keep_up = demo.parse_cli(["--all"])
        assert fixtures == demo.FIXTURES
        assert keep_up is False

    def test_keep_up_flag(self):
        fixtures, keep_up = demo.parse_cli(["clean.json", "--keep-up"])
        assert fixtures == ["clean.json"]
        assert keep_up is True

    def test_bare_name_gets_json_suffix(self):
        fixtures, _ = demo.parse_cli(["fraud"])
        assert fixtures == ["fraud.json"]

    def test_multiple_fixtures(self):
        fixtures, _ = demo.parse_cli(["clean.json", "deny"])
        assert fixtures == ["clean.json", "deny.json"]

    def test_no_fixture_raises(self):
        with pytest.raises(ValueError):
            demo.parse_cli([])

    def test_only_flags_raises(self):
        with pytest.raises(ValueError):
            demo.parse_cli(["--keep-up"])


class TestExtractRoomId:
    def test_parses_connect_line(self):
        line = "[Intake] connect OK - Room ID: b650bafb-4736-4e51-aefe-6dd0e1a0e616"
        assert demo.extract_room_id(line) == "b650bafb-4736-4e51-aefe-6dd0e1a0e616"

    def test_returns_none_for_other_lines(self):
        assert demo.extract_room_id("[Intake] framework=LangGraph vendor=Groq") is None
        assert demo.extract_room_id("") is None


class TestLineSignalsDone:
    def test_adjudicator_terminal_handoff(self):
        line = "[adjudicator] handoff -> ['nivishnick2k', 'nivishnick2k/intake']"
        assert demo.line_signals_done(line) is True

    def test_intermediate_handoffs_do_not_signal_done(self):
        assert (
            demo.line_signals_done("[intake] handoff -> ['nivishnick2k/coverage']")
            is False
        )
        assert (
            demo.line_signals_done("[fraud] handoff -> ['nivishnick2k/adjudicator']")
            is False
        )

    def test_unrelated_line(self):
        assert demo.line_signals_done("[coverage] processing claim CLM-CLEAN") is False


class TestExtractDecision:
    @pytest.mark.parametrize("status", ["APPROVE", "DENY", "ESCALATE"])
    def test_finds_each_status(self, status):
        trail = f'... "decision": {{\n    "status": "{status}",\n    "final_amount": 3700.0\n  }}'
        assert demo.extract_decision(trail) == status

    def test_returns_none_when_absent(self):
        assert demo.extract_decision('{"status": "expired"}') is None
        assert demo.extract_decision("") is None
