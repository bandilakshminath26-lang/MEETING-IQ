"""SQLAlchemy ORM models — the core business entities."""

from __future__ import annotations
import datetime as dt
from sqlalchemy import String, Text, Integer, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100))
    segment: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contacts: Mapped[list[Contact]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    company: Mapped[Company] = relationship(back_populates="contacts")
    meetings: Mapped[list[Meeting]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    emails: Mapped[list[Email]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    commitments: Mapped[list[Commitment]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    decisions: Mapped[list[Decision]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    concerns: Mapped[list[Concern]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    preferences: Mapped[list[Preference]] = relationship(back_populates="contact", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[str] = mapped_column(String(30), index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str] = mapped_column(String(20), ForeignKey("contacts.contact_id"), index=True)
    date: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    participants: Mapped[dict | list | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    topics: Mapped[dict | list | None] = mapped_column(JSON)
    transcript: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="synthetic")
    # New fields for upcoming-meeting workflow
    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="completed")
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    agenda: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact] = relationship(back_populates="meetings")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[str] = mapped_column(String(30), index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str] = mapped_column(String(20), ForeignKey("contacts.contact_id"), index=True)
    date: Mapped[str] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(500))
    sender: Mapped[str] = mapped_column(String(300))
    recipient: Mapped[str] = mapped_column(String(300))
    body: Mapped[str | None] = mapped_column(Text)
    related_meeting_id: Mapped[str | None] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(50), default="synthetic")
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact] = relationship(back_populates="emails")


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("contacts.contact_id"), nullable=True)
    meeting_id: Mapped[str | None] = mapped_column(String(30))
    date_created: Mapped[str] = mapped_column(String(20))
    owner: Mapped[str] = mapped_column(String(200))
    commitment: Mapped[str] = mapped_column(Text)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    evidence: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact | None] = relationship(back_populates="commitments")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("contacts.contact_id"), nullable=True)
    meeting_id: Mapped[str | None] = mapped_column(String(30))
    date: Mapped[str] = mapped_column(String(20))
    decision: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact | None] = relationship(back_populates="decisions")


class Concern(Base):
    __tablename__ = "concerns"

    id: Mapped[int] = mapped_column(primary_key=True)
    concern_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("contacts.contact_id"), nullable=True)
    meeting_id: Mapped[str | None] = mapped_column(String(30))
    date: Mapped[str] = mapped_column(String(20))
    concern: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact | None] = relationship(back_populates="concerns")


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    preference_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str] = mapped_column(String(20), ForeignKey("contacts.contact_id"), index=True)
    preference: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

    contact: Mapped[Contact] = relationship(back_populates="preferences")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    event_date: Mapped[str] = mapped_column(String(20), index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(30))
    title: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)


class RelationshipSnapshot(Base):
    __tablename__ = "relationship_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.customer_id"), index=True)
    company: Mapped[str] = mapped_column(String(200))
    contact: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(200))
    relationship_stage: Mapped[str] = mapped_column(String(50))
    primary_concern: Mapped[str | None] = mapped_column(Text)
    open_commitments: Mapped[int] = mapped_column(Integer, default=0)
    meeting_count: Mapped[int] = mapped_column(Integer, default=0)
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)


class HindsightMemory(Base):
    __tablename__ = "hindsight_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[str] = mapped_column(String(100), index=True)
    content: Mapped[str] = mapped_column(Text)
    customer_id: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    contact_id: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    event_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=dt.datetime.utcnow)

