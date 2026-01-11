from datetime import date, datetime
from sqlalchemy import func, Column, DateTime
from sqlmodel import SQLModel, Field
from typing import Optional


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
    billing_month: date = Field(description="Format: RRRR-MM-01")
    premia_start: date = Field(description="Data początkowa okresu premii")
    premia_end: date = Field(description="Data końcowa okresu premii")
    hours: dict
    comment: str
    status: str = "Waiting"