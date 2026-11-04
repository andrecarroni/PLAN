from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text)
    roles: Mapped[list] = mapped_column(JSON, default=lambda: ["aluno"])
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="pendente", index=True)
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class Session(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    csrf: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Reset(Base):
    __tablename__ = "reset_grants"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Attempt(Base):
    __tablename__ = "login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    since: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    start: Mapped[str] = mapped_column(String(7))
    selected_month: Mapped[str] = mapped_column(String(7))
    version: Mapped[int] = mapped_column(Integer, default=1)
    step: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[list] = mapped_column(JSON, default=list)
    card_mode: Mapped[str] = mapped_column(String(20), default="categorias")


class Category(Base):
    __tablename__ = "categories"
    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    label: Mapped[str] = mapped_column(String(160))
    suggestions: Mapped[list] = mapped_column(JSON)


class Entry(Base):
    __tablename__ = "entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(160))
    month: Mapped[str] = mapped_column(String(7))
    forecast: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    actual: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    deducted: Mapped[bool] = mapped_column(Boolean, default=False)
    method: Mapped[str] = mapped_column(String(20), default="outro")
    absent: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("plan_id", "key", "month"),)


class Debt(Base):
    __tablename__ = "debts"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64))
    institution: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(80))
    balance: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    installments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    guaranteed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str] = mapped_column(Text, default="")


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    deadline: Mapped[str | None] = mapped_column(String(10), nullable=True)
    negotiation: Mapped[str] = mapped_column(Text, default="")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    internal: Mapped[bool] = mapped_column(Boolean, default=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AccessEvent(Base):
    __tablename__ = "access_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Renewal(Base):
    __tablename__ = "renewals"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Content(Base):
    __tablename__ = "contents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    module: Mapped[str] = mapped_column(String(160))
    lesson: Mapped[str] = mapped_column(String(160))
    reference: Mapped[str] = mapped_column(String(200))
    context: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="rascunho")
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text)

class Opportunity(Base):
    __tablename__ = 'sales_opportunities'
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='CASCADE'),unique=True,index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id',ondelete='SET NULL'),nullable=True,index=True)
    stage: Mapped[str] = mapped_column(String(24),default='aguardando',index=True)
    cash_price: Mapped[Decimal] = mapped_column(Numeric(16,2),default=Decimal('5000.00'))
    installment_count: Mapped[int] = mapped_column(Integer,default=12)
    installment_value: Mapped[Decimal] = mapped_column(Numeric(16,2),default=Decimal('497.00'))
    selected_offer: Mapped[str | None] = mapped_column(String(20),nullable=True)
    next_contact: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True,index=True)
    notes: Mapped[str] = mapped_column(Text,default='')
    lost_reason: Mapped[str] = mapped_column(Text,default='')
    version: Mapped[int] = mapped_column(Integer,default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now,index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True,index=True)

class Appointment(Base):
    __tablename__ = 'sales_appointments'
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey('sales_opportunities.id',ondelete='CASCADE'),index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id',ondelete='SET NULL'),nullable=True,index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer,default=45)
    status: Mapped[str] = mapped_column(String(20),default='agendada',index=True)
    meeting_url: Mapped[str] = mapped_column(String(500),default='')
    notes: Mapped[str] = mapped_column(Text,default='')
    version: Mapped[int] = mapped_column(Integer,default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
