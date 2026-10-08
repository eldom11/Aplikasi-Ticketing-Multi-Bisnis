from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.user import UserBrief

Subject = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
Category = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
Body = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class TicketCreate(BaseModel):
    subject: Subject
    category: Category
    priority: TicketPriority
    message: Body 


class TicketUpdate(BaseModel):
    """Isi SALAH SATU: status ATAU assigned_agent_id."""

    status: TicketStatus | None = None
    assigned_agent_id: int | None = None

    @model_validator(mode="after")
    def exactly_one_field(self):
        if (self.status is None) == (self.assigned_agent_id is None):
            raise ValueError("Isi salah satu: status atau assigned_agent_id")
        return self


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    subject: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    customer: UserBrief
    assigned_agent: UserBrief | None