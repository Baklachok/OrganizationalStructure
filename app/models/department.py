from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "name",
            name="uq_departments_parent_name",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    parent: Mapped[Department | None] = relationship(
        "Department",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )
    employees: Mapped[list[Employee]] = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
    )
