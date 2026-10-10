import datetime
import uuid
from typing import Any, List, Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artifact, Chunk, Episode, Message, Session


class SessionRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        provider: str,
        model: str,
        user_id: str,
        title: str = "New Conversation",
    ) -> Session:
        session = Session(
            provider=provider,
            model=model,
            user_id=user_id,
            title=title,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get(self, session_id: uuid.UUID) -> Optional[Session]:
        stmt = select(Session).where(Session.id == session_id, Session.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, user_id: str) -> List[Session]:
        stmt = (
            select(Session)
            .where(Session.user_id == user_id, Session.deleted_at.is_(None))
            .order_by(Session.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, session_id: uuid.UUID) -> bool:
        stmt = (
            update(Session)
            .where(Session.id == session_id, Session.deleted_at.is_(None))
            .values(deleted_at=datetime.datetime.now(datetime.timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def set_sdk_session(self, session_id: uuid.UUID, sdk_session_id: str) -> None:
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(sdk_session_id=sdk_session_id, updated_at=datetime.datetime.now(datetime.timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def touch(self, session_id: uuid.UUID, title: Optional[str] = None) -> None:
        values: dict[str, Any] = {"updated_at": datetime.datetime.now(datetime.timezone.utc)}
        if title:
            values["title"] = title
        stmt = update(Session).where(Session.id == session_id).values(**values)
        await self.db.execute(stmt)
        await self.db.flush()


class MessageRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        citations: Optional[List[dict[str, Any]]] = None,
        stats: Optional[dict[str, Any]] = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations or [],
            stats=stats or {},
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def for_session(self, session_id: uuid.UUID) -> List[Message]:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ArtifactRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: uuid.UUID,
        kind: str,
        title: str,
        content: str,
        message_id: Optional[int] = None,
    ) -> Artifact:
        artifact = Artifact(
            artifact_group_id=uuid.uuid4(),
            session_id=session_id,
            message_id=message_id,
            version=1,
            kind=kind,
            title=title,
            content=content,
        )
        self.db.add(artifact)
        await self.db.flush()
        return artifact

    async def add_version(
        self,
        group_id: uuid.UUID,
        content: str,
        title: Optional[str] = None,
        change_note: Optional[str] = None,
    ) -> Artifact:
        # Find latest version in group
        latest_stmt = (
            select(Artifact)
            .where(Artifact.artifact_group_id == group_id)
            .order_by(Artifact.version.desc())
            .limit(1)
        )
        res = await self.db.execute(latest_stmt)
        latest = res.scalar_one_or_none()
        if not latest:
            raise ValueError(f"Artifact group {group_id} not found")

        new_version = latest.version + 1
        artifact = Artifact(
            artifact_group_id=group_id,
            session_id=latest.session_id,
            message_id=latest.message_id,
            version=new_version,
            kind=latest.kind,
            title=title or latest.title,
            content=content,
            change_note=change_note,
        )
        self.db.add(artifact)
        await self.db.flush()
        return artifact

    async def groups_for_session(self, session_id: uuid.UUID) -> List[Artifact]:
        """Returns the latest version of each artifact group in this session."""
        # Query distinct group latest versions
        subq = (
            select(
                Artifact.artifact_group_id,
                func.max(Artifact.version).label("max_version"),
            )
            .where(Artifact.session_id == session_id)
            .group_by(Artifact.artifact_group_id)
            .subquery()
        )

        stmt = select(Artifact).join(
            subq,
            (Artifact.artifact_group_id == subq.c.artifact_group_id)
            & (Artifact.version == subq.c.max_version),
        ).order_by(Artifact.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_version(self, group_id: uuid.UUID, version: int) -> Optional[Artifact]:
        stmt = select(Artifact).where(
            Artifact.artifact_group_id == group_id,
            Artifact.version == version,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_versions(self, group_id: uuid.UUID) -> List[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.artifact_group_id == group_id)
            .order_by(Artifact.version.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ChunkRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_episode(self, meta: dict[str, Any]) -> int:
        stmt = (
            insert(Episode)
            .values(
                slug=meta["slug"],
                guest=meta.get("guest"),
                title=meta.get("title"),
                youtube_url=meta.get("youtube_url"),
                video_id=meta.get("video_id"),
                publish_date=meta.get("publish_date"),
                duration_seconds=meta.get("duration_seconds"),
                keywords=meta.get("keywords"),
                description=meta.get("description"),
                content_hash=meta.get("content_hash"),
            )
            .on_conflict_do_update(
                index_elements=["slug"],
                set_={
                    "guest": meta.get("guest"),
                    "title": meta.get("title"),
                    "youtube_url": meta.get("youtube_url"),
                    "video_id": meta.get("video_id"),
                    "publish_date": meta.get("publish_date"),
                    "duration_seconds": meta.get("duration_seconds"),
                    "keywords": meta.get("keywords"),
                    "description": meta.get("description"),
                    "content_hash": meta.get("content_hash"),
                },
            )
            .returning(Episode.id)
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.scalar_one()

    async def upsert_chunks(self, episode_id: int, chunks: List[dict[str, Any]]) -> int:
        if not chunks:
            return 0
        inserted_count = 0
        for c in chunks:
            stmt = (
                insert(Chunk)
                .values(
                    episode_id=episode_id,
                    chunk_index=c["chunk_index"],
                    text=c["text"],
                    token_count=c.get("token_count"),
                    start_ts=c.get("start_ts"),
                    speaker=c.get("speaker"),
                    embedding=c.get("embedding"),
                    content_hash=c.get("content_hash"),
                )
                .on_conflict_do_nothing(index_elements=["content_hash"])
            )
            res = await self.db.execute(stmt)
            if res.rowcount > 0:
                inserted_count += 1
        await self.db.flush()
        return inserted_count

    async def count(self) -> int:
        res = await self.db.execute(select(func.count(Chunk.id)))
        return res.scalar_one() or 0
