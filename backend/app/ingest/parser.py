import re
from dataclasses import dataclass
from typing import Any, List

import frontmatter


@dataclass
class Turn:
    speaker: str
    ts_seconds: int
    text: str


@dataclass
class ParsedEpisode:
    meta: dict[str, Any]
    turns: List[Turn]


TURN_HEADER_REGEX = re.compile(
    r"^(?:(?P<speaker>[^\n\r(]+?)[ \t]*)?\((?P<ts>\d{1,2}:\d{2}(?::\d{2})?)\):[ \t]*$",
    re.MULTILINE,
)


def ts_to_seconds(ts_str: str) -> int:
    """Converts 'HH:MM:SS' or 'MM:SS' into integer seconds."""
    parts = [int(p) for p in ts_str.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return parts[0]
    raise ValueError(f"Invalid timestamp format: {ts_str}")


def parse_transcript(raw: str) -> ParsedEpisode:
    """Parses episode markdown containing YAML frontmatter and speaker turn blocks."""
    post = frontmatter.loads(raw)
    if not post.metadata:
        raise ValueError("Transcript lacks YAML frontmatter")

    body = post.content
    # Find all speaker turn headings
    matches = list(TURN_HEADER_REGEX.finditer(body))
    turns: List[Turn] = []
    current_speaker = "Unknown"

    for i, match in enumerate(matches):
        raw_speaker = match.group("speaker")
        ts_str = match.group("ts")
        speaker = raw_speaker.strip() if raw_speaker else current_speaker
        current_speaker = speaker
        ts_seconds = ts_to_seconds(ts_str)

        start_content = match.end()
        end_content = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        turn_text = body[start_content:end_content].strip()

        if turn_text:
            turns.append(Turn(speaker=speaker, ts_seconds=ts_seconds, text=turn_text))

    return ParsedEpisode(meta=dict(post.metadata), turns=turns)
