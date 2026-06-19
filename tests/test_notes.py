import asyncio
from types import SimpleNamespace

import pytest

from claimband import notes


def test_parse_narrative_risk_response_parses_and_clamps():
    assert notes._parse_narrative_risk_response("RISK=12 | plausible") == (
        12,
        "plausible",
    )
    assert notes._parse_narrative_risk_response("RISK=99 | too high") == (
        40,
        "too high",
    )


def test_parse_narrative_risk_response_falls_back_on_bad_output():
    assert notes._parse_narrative_risk_response("no structured answer") == (0, "")
    assert notes._parse_narrative_risk_response("RISK=abc | broken") == (0, "")


def test_groq_narrative_risk_uses_parsed_response(monkeypatch: pytest.MonkeyPatch):
    async def fake_create(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="RISK=17 | story is plausible")
                )
            ]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(notes, "AsyncOpenAI", lambda **_kwargs: fake_client)

    risk, rationale = asyncio.run(notes.groq_narrative_risk("summary text"))
    assert risk == 17
    assert rationale == "story is plausible"


def test_groq_narrative_risk_falls_back_on_bad_output(monkeypatch: pytest.MonkeyPatch):
    async def fake_create(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=""))]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(notes, "AsyncOpenAI", lambda **_kwargs: fake_client)

    risk, rationale = asyncio.run(notes.groq_narrative_risk("summary text"))
    assert risk == 0
    assert rationale == ""
