"""SQLAlchemy ORM models — Phase 1 database foundation."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base

# Dimensi embedding Voyage-3-large (digunakan di Phase 3)
EMBEDDING_DIMS = 1024


class User(Base):
    __tablename__ = "users"

    # server_default memastikan gen_random_uuid() jadi DEFAULT di PostgreSQL
    # sehingga raw SQL INSERT tanpa kolom 'id' tetap bekerja.
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    org_name      = Column(String(255), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    postmortems = relationship("Postmortem", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Postmortem(Base):
    __tablename__ = "postmortems"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"), nullable=False)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title            = Column(String(500), nullable=False)
    incident_date    = Column(String(10), nullable=False)   # ISO-8601: "2025-03-15"
    raw_content      = Column(Text, nullable=False)
    summary          = Column(Text, nullable=True)
    root_causes      = Column(JSONB, nullable=True)          # list[str]
    action_items     = Column(JSONB, nullable=True)          # list[{description, owner, status, ticket_ref}]
    severity         = Column(String(10), CheckConstraint("severity IN ('P0','P1','P2','P3')", name="ck_postmortems_severity"), nullable=True)
    systems_affected = Column(JSONB, nullable=True)          # list[str]
    embedding        = Column(Vector(EMBEDDING_DIMS), nullable=True)
    has_recurrence   = Column(Boolean, default=False, nullable=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="postmortems")

    def __repr__(self) -> str:
        return f"<Postmortem id={self.id} title={self.title!r}>"
