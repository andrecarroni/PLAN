import re
from typing import Literal
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .finance import money, months, CODES

Role = Literal["aluno", "consultor", "vendedor", "administrador"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Strict):
    phone: str = Field(max_length=20)
    password: str = Field(max_length=200)


class UserInput(Strict):
    name: str = Field(min_length=2, max_length=160)
    phone: str
    email: str | None = Field(default=None, max_length=254)
    password: str = Field(min_length=12, max_length=200)
    roles: list[Role] = Field(default=["aluno"], min_length=1, max_length=4)

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v):
        if not re.fullmatch(r"\+[1-9]\d{7,14}", v):
            raise ValueError("Use +, código do país e DDD, sem espaços.")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        if v and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v):
            raise ValueError("E-mail inválido.")
        return v or None


class Roles(Strict):
    roles: list[Role] = Field(min_length=1, max_length=4)


class Enabled(Strict):
    enabled: bool


class Access(Strict):
    action: Literal["ativar", "renovar", "bloquear", "revogar"]
    expires_at: datetime | None = None


class Password(Strict):
    old_password: str = Field(max_length=200)
    password: str = Field(min_length=12, max_length=200)


class ResetInput(Strict):
    token: str = Field(max_length=100)
    password: str = Field(min_length=12, max_length=200)


class EntryInput(Strict):
    key: str = Field(min_length=1, max_length=64)
    category: Literal[
        "rendas", "bancarias", "consignados", "fixas", "variaveis", "eventuais"
    ]
    label: str = Field(min_length=1, max_length=160)
    month: str
    forecast: str | None = None
    actual: str | None = None
    deducted: bool = False
    method: Literal["outro", "cartao", "fatura"] = "outro"
    absent: bool = False

    @field_validator("forecast", "actual")
    @classmethod
    def amount(cls, v):
        d = money(v)
        return str(d) if d is not None else None


class DebtInput(Strict):
    key: str = Field(min_length=1, max_length=64)
    institution: str = Field(min_length=1, max_length=160)
    kind: str = Field(min_length=1, max_length=80)
    balance: str | None = None
    installments: int | None = Field(default=None, ge=0, le=1200)
    end: date | None = None
    guaranteed: bool = False
    status: str = Field(default="A informar", max_length=80)
    notes: str = Field(default="", max_length=5000)

    @field_validator("balance")
    @classmethod
    def amount(cls, v):
        d = money(v)
        return str(d) if d is not None else None


class GoalInput(Strict):
    title: str = Field(min_length=1, max_length=160)
    amount: str | None = None
    deadline: date | None = None
    negotiation: str = Field(default="", max_length=5000)

    @field_validator("amount")
    @classmethod
    def amount_valid(cls, v):
        d = money(v)
        return str(d) if d is not None else None


class PlanInput(Strict):
    version: int = Field(ge=1)
    start: str
    selected_month: str
    step: int = Field(ge=0, le=7)
    completed: list[int] = Field(max_length=8)
    card_mode: Literal["categorias", "fatura"] = "categorias"
    entries: list[EntryInput] = Field(max_length=2400)
    debts: list[DebtInput] = Field(default=[], max_length=200)
    goals: list[GoalInput] = Field(default=[], max_length=100)

    @model_validator(mode="after")
    def valid(self):
        if not re.fullmatch(r"\d{4}-\d{2}", self.start):
            raise ValueError("Mês inicial inválido.")
        ms = months(self.start)
        if self.selected_month not in ms or any(
            e.month not in ms for e in self.entries
        ):
            raise ValueError("Mês fora do período de 12 meses.")
        if len(set(self.completed)) != len(self.completed) or any(
            i < 0 or i > 7 for i in self.completed
        ):
            raise ValueError("Etapas inválidas.")
        if len({(e.key, e.month) for e in self.entries}) != len(self.entries):
            raise ValueError("Lançamento repetido.")
        if len({d.key for d in self.debts}) != len(self.debts):
            raise ValueError("Dívida repetida.")
        for e in self.entries:
            if e.absent and (
                money(e.forecast) not in (None, 0) or money(e.actual) not in (None, 0)
            ):
                raise ValueError("Item não existente não pode ter valores.")
            if e.deducted and e.category != "consignados":
                raise ValueError("Desconto em folha deve estar em consignados.")
        return self


class NoteInput(Strict):
    text: str = Field(min_length=1, max_length=10000)
    internal: bool = True


class ContentInput(Strict):
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=15000)
    module: str = Field(min_length=1, max_length=160)
    lesson: str = Field(min_length=1, max_length=160)
    reference: str = Field(min_length=1, max_length=200)
    context: str = Field(max_length=20)
    version: int = Field(default=1, ge=1)
    status: Literal["rascunho", "publicado"] = "rascunho"


class Support(Strict):
    contact: str = Field(max_length=500)


class CSVInput(Strict):
    text: str = Field(max_length=1000000)
    commit: bool = False


class DeleteInput(Strict):
    confirmation: str
    reason: str = Field(min_length=10, max_length=500)
