import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import List

from app.ingest.parser import Turn


@dataclass
class ChunkDraft:
    text: str
    start_ts: int
    speaker: str
    chunk_index: int
    token_count: int
    content_hash: str


SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")


def approx_tokens(text: str) -> int:
    """Heuristic token count estimation: ~4 chars per token."""
    return max(1, len(text) // 4)


def _split_long_turn(turn: Turn, max_tokens: int) -> List[Turn]:
    """Splits an oversized single turn into smaller pieces on sentence boundaries."""
    sentences = SENTENCE_SPLIT_REGEX.split(turn.text)
    sub_turns: List[Turn] = []
    current_sentences: List[str] = []
    current_tokens = 0

    for s in sentences:
        s_tokens = approx_tokens(s)
        if current_tokens + s_tokens > max_tokens and current_sentences:
            sub_turns.append(
                Turn(speaker=turn.speaker, ts_seconds=turn.ts_seconds, text=" ".join(current_sentences))
            )
            current_sentences = [s]
            current_tokens = s_tokens
        else:
            current_sentences.append(s)
            current_tokens += s_tokens

    if current_sentences:
        sub_turns.append(
            Turn(speaker=turn.speaker, ts_seconds=turn.ts_seconds, text=" ".join(current_sentences))
        )
    return sub_turns


def chunk_turns(
    turns: List[Turn],
    target_tokens: int = 600,
    max_tokens: int = 900,
    overlap_turns: int = 1,
) -> List[ChunkDraft]:
    """Greedily groups speaker turns into chunks respecting token budgets and turn overlaps."""
    if not turns:
        return []

    # Flatten turns with over-long turns split
    normalized_turns: List[Turn] = []
    for t in turns:
        if approx_tokens(t.text) > max_tokens:
            normalized_turns.extend(_split_long_turn(t, max_tokens))
        else:
            normalized_turns.append(t)

    chunks: List[ChunkDraft] = []
    current_window: List[Turn] = []
    current_tokens = 0
    chunk_index = 0

    i = 0
    while i < len(normalized_turns):
        turn = normalized_turns[i]
        turn_tokens = approx_tokens(f"{turn.speaker}: {turn.text}")

        if current_tokens + turn_tokens > target_tokens and current_window:
            # Build chunk from current_window
            chunk_text = "\n\n".join(f"{t.speaker}: {t.text}" for t in current_window)
            c_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16]
            speaker_chars: dict[str, int] = defaultdict(int)
            for t in current_window:
                speaker_chars[t.speaker] += len(t.text)
            primary_speaker = max(speaker_chars.items(), key=lambda kv: kv[1])[0]

            chunks.append(
                ChunkDraft(
                    text=chunk_text,
                    start_ts=current_window[0].ts_seconds,
                    speaker=primary_speaker,
                    chunk_index=chunk_index,
                    token_count=approx_tokens(chunk_text),
                    content_hash=c_hash,
                )
            )
            chunk_index += 1

            # Prepare next window starting with overlap turns
            if overlap_turns > 0 and len(current_window) > overlap_turns:
                current_window = current_window[-overlap_turns:]
                current_tokens = sum(approx_tokens(f"{t.speaker}: {t.text}") for t in current_window)
            else:
                current_window = []
                current_tokens = 0

        current_window.append(turn)
        current_tokens += turn_tokens
        i += 1

    if current_window:
        chunk_text = "\n\n".join(f"{t.speaker}: {t.text}" for t in current_window)
        c_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16]
        speaker_chars = defaultdict(int)
        for t in current_window:
            speaker_chars[t.speaker] += len(t.text)
        primary_speaker = max(speaker_chars.items(), key=lambda kv: kv[1])[0]

        chunks.append(
            ChunkDraft(
                text=chunk_text,
                start_ts=current_window[0].ts_seconds,
                speaker=primary_speaker,
                chunk_index=chunk_index,
                token_count=approx_tokens(chunk_text),
                content_hash=c_hash,
            )
        )

    return chunks
