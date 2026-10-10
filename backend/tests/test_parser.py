from pathlib import Path
import pytest
from app.ingest.parser import parse_transcript, ts_to_seconds

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_transcript.md"


def test_ts_to_seconds():
    assert ts_to_seconds("00:00:00") == 0
    assert ts_to_seconds("00:01:21") == 81
    assert ts_to_seconds("01:02:33") == 3753
    assert ts_to_seconds("02:33") == 153


def test_parse_transcript():
    raw = FIXTURE_PATH.read_text(encoding="utf-8")
    parsed = parse_transcript(raw)

    assert parsed.meta["guest"] == "Ada Chen Rekhi"
    assert parsed.meta["title"] == "How to Find Your True North"
    assert len(parsed.turns) == 4

    # Check continuation inherited Lenny
    assert parsed.turns[0].speaker == "Ada Chen Rekhi"
    assert parsed.turns[0].ts_seconds == 0

    assert parsed.turns[1].speaker == "Lenny"
    assert parsed.turns[1].ts_seconds == 36

    assert parsed.turns[2].speaker == "Lenny"
    assert parsed.turns[2].ts_seconds == 81
    assert "coaching versus mentoring" in parsed.turns[2].text

    assert parsed.turns[3].speaker == "Ada Chen Rekhi"
    assert parsed.turns[3].ts_seconds == 105


def test_parse_transcript_missing_frontmatter():
    with pytest.raises(ValueError):
        parse_transcript("Just raw text with no YAML frontmatter")
