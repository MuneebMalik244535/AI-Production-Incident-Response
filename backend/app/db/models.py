"""SQLAlchemy ORM models for DB persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentModel(Base):
    """Incident ORM table."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RECEIVED")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    agent_runs: Mapped[list[AgentRunModel]] = relationship("AgentRunModel", back_populates="incident", cascade="all, delete-orphan")
    findings: Mapped[list[FindingModel]] = relationship("FindingModel", back_populates="incident", cascade="all, delete-orphan")
    recommendation: Mapped[RecommendationModel | None] = relationship("RecommendationModel", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    approvals: Mapped[list[ApprovalModel]] = relationship("ApprovalModel", back_populates="incident", cascade="all, delete-orphan")


class AgentRunModel(Base):
    """Agent Run execution log table."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUCCESS")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    incident: Mapped[IncidentModel] = relationship("IncidentModel", back_populates="agent_runs")


class FindingModel(Base):
    """Investigation findings table."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    incident: Mapped[IncidentModel] = relationship("IncidentModel", back_populates="findings")


class RecommendationModel(Base):
    """Recommendation ORM table."""

    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False, unique=True)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_actions: Mapped[list[Any]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    suggested_pr_description: Mapped[str] = mapped_column(Text, default="")
    requires_immediate_action: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    incident: Mapped[IncidentModel] = relationship("IncidentModel", back_populates="recommendation")


class ApprovalModel(Base):
    """Human approval decision table."""

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # APPROVE / REJECT / ESCALATE
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    incident: Mapped[IncidentModel] = relationship("IncidentModel", back_populates="approvals")
