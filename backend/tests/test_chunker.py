from app.ingest.chunker import approx_tokens, chunk_turns
from app.ingest.parser import Turn


def test_approx_tokens():
    assert approx_tokens("hello world") == 2
    assert approx_tokens("") == 1


def test_chunk_turns_grouping():
    turns = [
        Turn(speaker="Lenny", ts_seconds=0, text="First turn that is relatively short."),
        Turn(speaker="Guest", ts_seconds=10, text="Second turn that explains something clear."),
        Turn(speaker="Guest", ts_seconds=20, text="Third turn offering more details and advice."),
    ]
    chunks = chunk_turns(turns, target_tokens=30, max_tokens=100, overlap_turns=1)
    assert len(chunks) >= 1
    assert all(c.token_count > 0 for c in chunks)
    assert all(len(c.content_hash) == 16 for c in chunks)
    assert chunks[0].speaker in ("Lenny", "Guest")


def test_chunk_turns_split_oversized():
    long_text = "This is sentence one. " * 50
    turns = [
        Turn(speaker="Guest", ts_seconds=0, text=long_text)
    ]
    chunks = chunk_turns(turns, target_tokens=50, max_tokens=80, overlap_turns=0)
    assert len(chunks) > 1
    # Verify indexes sequential
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
