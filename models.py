from datetime import date, datetime
from sqlalchemy import func, Column, DateTime, JSON, String
from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any


class Wniosek(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    person: str
    company: str
    type_of_woz: str
    payoff: float
    created_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        default_factory=datetime.now
    )
    owner: Optional[str] = Field(default=None)
    # Daty jako stringi dla kompatybilności z SQLite (format: YYYY-MM-DD)
    billing_month: Optional[str] = Field(default=None, description="Format: RRRR-MM-DD")
    premia_start: Optional[str] = Field(default=None, description="Data początkowa okresu premii")
    premia_end: Optional[str] = Field(default=None, description="Data końcowa okresu premii")
    hours: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    comment: Optional[str] = Field(default="")
    status: str = "Waiting"


class User(SQLModel, table=True):
    """Model użytkownika w bazie danych."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, index=True))
    password_hash: str
    full_name: str
    role: str = Field(default="user")  # user, payroll, admin
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)