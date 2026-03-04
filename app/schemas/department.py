from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class DepartmentCreate(DepartmentBase):
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None
