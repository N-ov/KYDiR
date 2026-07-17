from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, Field, field_validator

TxType = Literal["expense", "income"]

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


def to_kopecks(amount: float) -> int:
    return int(round(amount * 100))


def from_kopecks(kopecks: int) -> float:
    return kopecks / 100


# --- auth / users ---

class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    color: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=4)
    color: str = Field(default="#4f8ef7", pattern=HEX_COLOR)

    @field_validator("username")
    @classmethod
    def username_lower(cls, v: str) -> str:
        return v.strip().lower()


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    password: str | None = Field(default=None, min_length=4)


# --- categories ---

class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: TxType
    icon: str = Field(default="📦", max_length=16)
    color: str = Field(default="#8884d8", pattern=HEX_COLOR)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=16)
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    archived: bool | None = None


class CategoryOut(CategoryBase):
    id: int
    archived: bool

    model_config = {"from_attributes": True}


# --- transactions ---

class TransactionCreate(BaseModel):
    amount: float = Field(gt=0, description="Сумма в рублях, например 123.45")
    type: TxType
    category_id: int
    date: date_type
    comment: str = Field(default="", max_length=500)


class TransactionUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    category_id: int | None = None
    date: date_type | None = None
    comment: str | None = Field(default=None, max_length=500)


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TxType
    date: date_type
    comment: str
    category: CategoryOut
    user: UserOut


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    per_page: int
    pages: int


# --- analytics ---

class CategoryTotal(BaseModel):
    category_id: int
    name: str
    icon: str
    color: str
    total: float
    count: int


class UserTotal(BaseModel):
    user_id: int
    display_name: str
    color: str
    total: float


class Summary(BaseModel):
    date_from: date_type
    date_to: date_type
    income_total: float
    expense_total: float
    balance: float
    expense_by_category: list[CategoryTotal]
    income_by_category: list[CategoryTotal]
    expense_by_user: list[UserTotal]


class MonthPoint(BaseModel):
    month: str  # "2026-07"
    income: float
    expense: float
