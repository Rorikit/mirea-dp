from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AttendanceType,
    ErrorSeverity,
    EventStatus,
    ImportAction,
    ImportStatus,
    PresenceStatus,
    QrPurpose,
    QrStatus,
    UserRole,
    ValidationStatus,
)


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.DRAFT)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    scanning_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="event_time_order"),)


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(BigInteger)
    file_hash: Mapped[str] = mapped_column(String(64))
    uploaded_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus), default=ImportStatus.UPLOADED)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_rows: Mapped[int] = mapped_column(Integer, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_rows: Mapped[int] = mapped_column(Integer, default=0)
    deactivated_rows: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preview_version: Mapped[str | None] = mapped_column(String(64))


class SourceStudent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_students"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(128))
    full_name: Mapped[str] = mapped_column(String(300))
    normalized_full_name: Mapped[str] = mapped_column(String(300))
    study_group: Mapped[str] = mapped_column(String(100))
    normalized_study_group: Mapped[str] = mapped_column(String(100))
    institute: Mapped[str] = mapped_column(String(300))
    normalized_institute: Mapped[str] = mapped_column(String(300))
    source_row_number: Mapped[int | None] = mapped_column(Integer)
    import_batch_id: Mapped[UUID | None] = mapped_column(ForeignKey("import_batches.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("event_id", "source_id"),
        Index(
            "ix_students_registration_lookup",
            "event_id",
            "normalized_full_name",
            "normalized_study_group",
            postgresql_where=text("is_active"),
        ),
        Index("ix_students_group", "event_id", "normalized_study_group"),
        Index("ix_students_institute", "event_id", "normalized_institute"),
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_sessions"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    user: Mapped[User] = relationship()


class Registration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "registrations"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    source_student_id: Mapped[UUID] = mapped_column(ForeignKey("source_students.id"))
    public_id: Mapped[UUID] = mapped_column(default=uuid4, unique=True)
    presence_status: Mapped[PresenceStatus] = mapped_column(
        Enum(PresenceStatus), default=PresenceStatus.OUTSIDE
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_student: Mapped[SourceStudent] = relationship()
    __table_args__ = (UniqueConstraint("event_id", "source_student_id"),)


class StudentSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "student_sessions"
    registration_id: Mapped[UUID] = mapped_column(ForeignKey("registrations.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class QrToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "qr_tokens"
    registration_id: Mapped[UUID] = mapped_column(ForeignKey("registrations.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[QrPurpose] = mapped_column(Enum(QrPurpose))
    status: Mapped[QrStatus] = mapped_column(Enum(QrStatus), default=QrStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_operator_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        Index(
            "uq_qr_active_registration",
            "registration_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )


class AttendanceEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attendance_events"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    registration_id: Mapped[UUID] = mapped_column(ForeignKey("registrations.id"), index=True)
    operator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    qr_token_id: Mapped[UUID] = mapped_column(ForeignKey("qr_tokens.id"), unique=True)
    event_type: Mapped[AttendanceType] = mapped_column(Enum(AttendanceType))
    previous_status: Mapped[PresenceStatus] = mapped_column(Enum(PresenceStatus))
    new_status: Mapped[PresenceStatus] = mapped_column(Enum(PresenceStatus))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    request_id: Mapped[UUID] = mapped_column(unique=True)
    device_info: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScanAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scan_attempts"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    operator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    qr_token_id: Mapped[UUID | None] = mapped_column(ForeignKey("qr_tokens.id"))
    registration_id: Mapped[UUID | None] = mapped_column(ForeignKey("registrations.id"))
    result: Mapped[str] = mapped_column(String(50))
    error_code: Mapped[str | None] = mapped_column(String(100))
    request_id: Mapped[UUID] = mapped_column()
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    response_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    device_info: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("operator_id", "idempotency_key"),)


class ImportRow(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "import_rows"
    import_batch_id: Mapped[UUID] = mapped_column(ForeignKey("import_batches.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[str | None] = mapped_column(String(128))
    name: Mapped[str | None] = mapped_column(String(300))
    group: Mapped[str | None] = mapped_column(String(100))
    institute: Mapped[str | None] = mapped_column(String(300))
    normalized_name: Mapped[str | None] = mapped_column(String(300))
    normalized_group: Mapped[str | None] = mapped_column(String(100))
    normalized_institute: Mapped[str | None] = mapped_column(String(300))
    action: Mapped[ImportAction] = mapped_column(Enum(ImportAction))
    validation_status: Mapped[ValidationStatus] = mapped_column(Enum(ValidationStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("import_batch_id", "row_number"),)


class ImportRowError(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "import_row_errors"
    import_batch_id: Mapped[UUID] = mapped_column(ForeignKey("import_batches.id"), index=True)
    import_row_id: Mapped[UUID | None] = mapped_column(ForeignKey("import_rows.id"))
    row_number: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str] = mapped_column(String(100))
    error_message: Mapped[str] = mapped_column(String(500))
    severity: Mapped[ErrorSeverity] = mapped_column(Enum(ErrorSeverity))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScheduleItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "schedule_items"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    map_zone_id: Mapped[UUID | None] = mapped_column()
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="schedule_time_order"),)


class MapAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "map_assets"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    original_name: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    uploaded_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        Index("uq_active_map_event", "event_id", unique=True, postgresql_where=text("is_active")),
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    object_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[str | None] = mapped_column(String(100))
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    request_id: Mapped[UUID] = mapped_column(index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
