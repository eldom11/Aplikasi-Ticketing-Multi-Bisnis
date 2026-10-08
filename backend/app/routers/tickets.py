from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_role
from app.models import User
from app.models.enums import Role, TicketStatus
from app.schemas.ticket import TicketCreate, TicketOut, TicketUpdate
from app.services import tickets as tickets_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return tickets_service.list_tickets(db, user, status_filter)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate,
    customer: User = Depends(require_role(Role.customer)),
    db: Session = Depends(get_db),
):
    return tickets_service.create_ticket(db, customer, data)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return tickets_service.get_ticket_for_user(db, user, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return tickets_service.update_ticket(db, user, ticket_id, data)