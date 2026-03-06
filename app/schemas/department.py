from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DepartmentBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)


class DepartmentCreate(DepartmentBase):
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None


class DepartmentGetQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depth: int = Field(default=1, ge=1, le=5)
    include_employees: bool = True


class DepartmentDeleteQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["cascade", "reassign"] = "cascade"
    reassign_to_department_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_reassign_mode(self) -> DepartmentDeleteQuery:
        if self.mode == "reassign" and self.reassign_to_department_id is None:
            raise ValueError("reassign_to_department_id is required when mode is 'reassign'")
        if self.mode == "cascade" and self.reassign_to_department_id is not None:
            raise ValueError("reassign_to_department_id is only allowed when mode is 'reassign'")
        return self
