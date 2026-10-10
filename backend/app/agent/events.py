import json
from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class TokenEvent:
    text: str
    type: str = "token"

    def to_sse(self) -> str:
        return f"event: token\ndata: {json.dumps({'text': self.text})}\n\n"


@dataclass
class StatusEvent:
    message: str
    type: str = "status"

    def to_sse(self) -> str:
        return f"event: status\ndata: {json.dumps({'message': self.message})}\n\n"


@dataclass
class CitationEvent:
    chunk_id: int
    guest: str
    title: str
    episode_slug: str
    start_ts: int
    youtube_url: str
    snippet: str
    type: str = "citation"

    def to_sse(self) -> str:
        data = asdict(self)
        del data["type"]
        return f"event: citation\ndata: {json.dumps(data)}\n\n"


@dataclass
class ArtifactEvent:
    id: int
    group_id: str
    version: int
    kind: str
    title: str
    content: str
    change_note: Optional[str] = None
    type: str = "artifact"

    def to_sse(self) -> str:
        data = asdict(self)
        del data["type"]
        return f"event: artifact\ndata: {json.dumps(data)}\n\n"


@dataclass
class DoneEvent:
    message_id: int
    stats: dict[str, Any]
    type: str = "done"

    def to_sse(self) -> str:
        return f"event: done\ndata: {json.dumps({'message_id': self.message_id, 'stats': self.stats})}\n\n"


@dataclass
class ErrorEvent:
    code: str
    message: str
    detail: Optional[dict[str, Any]] = None
    type: str = "error"

    def to_sse(self) -> str:
        return f"event: error\ndata: {json.dumps({'error': {'code': self.code, 'message': self.message, 'detail': self.detail or {}}})}\n\n"
