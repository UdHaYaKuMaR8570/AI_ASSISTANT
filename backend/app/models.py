import datetime
import uuid
from typing import Any, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    guest: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    youtube_url: Mapped[Optional[str]] = mapped_column(Text)
    video_id: Mapped[Optional[str]] = mapped_column(Text)
    publish_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    description: Mapped[Optional[str]] = mapped_column(Text)
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
    content_hash: Mapped[Optional[str]] = mapped_column(Text)

    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="episode", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    start_ts: Mapped[Optional[int]] = mapped_column(Integer)
    speaker: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768))
    content_hash: Mapped[Optional[str]] = mapped_column(Text, unique=True)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="chunks")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="ollama")
    model: Mapped[str] = mapped_column(Text, nullable=False, default="qwen3:4b")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="New Conversation")
    sdk_session_id: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), onupdate=func.clock_timestamp()
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))

    messages: Mapped[List["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[List[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )

    session: Mapped["Session"] = relationship("Session", back_populates="messages")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_group_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("messages.id", ondelete="SET NULL"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="markdown")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )

    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")
