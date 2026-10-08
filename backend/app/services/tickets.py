from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Message, Ticket, User
from app.models.business import utcnow
from app.models.enums import Role, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate

STATUS_TRANSITIONS = {
    (TicketStatus.in_progress, TicketStatus.resolved): {Role.agent, Role.admin},
    (TicketStatus.resolved, TicketStatus.closed): {Role.agent, Role.admin},
    (TicketStatus.resolved, TicketStatus.open): {Role.customer},
}


def _visible_tickets(user: User):
    """Query dasar: HANYA tiket yang boleh dilihat user ini."""
    stmt = (
        select(Ticket)
        .where(Ticket.business_id == user.business_id)
        .options(joinedload(Ticket.customer), joinedload(Ticket.assigned_agent))
    )
    if user.role == Role.customer:
        stmt = stmt.where(Ticket.customer_id == user.id)
    return stmt


def get_ticket_for_user(db: Session, user: User, ticket_id: int) -> Ticket:
    """Pintu tunggal akses tiket. Dipakai SEMUA endpoint tiket, pesan, dan WebSocket.
    Tiket bisnis lain / customer lain => 404 (bukan 403, supaya keberadaannya tidak bocor)."""
    ticket = db.scalar(_visible_tickets(user).where(Ticket.id == ticket_id))
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tiket tidak ditemukan")
    return ticket


def list_tickets(
    db: Session, user: User, status_filter: TicketStatus | None
) -> list[Ticket]:
    stmt = _visible_tickets(user)
    if status_filter is not None:
        stmt = stmt.where(Ticket.status == status_filter)
    stmt = stmt.order_by(Ticket.updated_at.desc(), Ticket.id.desc())
    return list(db.scalars(stmt))


def create_ticket(db: Session, customer: User, data: TicketCreate) -> Ticket:
    ticket = Ticket(
        business_id=customer.business_id, 
        customer_id=customer.id,
        subject=data.subject,
        category=data.category,
        priority=data.priority,
        status=TicketStatus.open,
    )
    ticket.messages.append(Message(sender_id=customer.id, body=data.message))
    db.add(ticket)  
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, user: User, ticket_id: int, data: TicketUpdate) -> Ticket:
    ticket = get_ticket_for_user(db, user, ticket_id)
    if data.assigned_agent_id is not None:
        _assign(db, user, ticket, data.assigned_agent_id)
    else:
        _change_status(user, ticket, data.status)
    ticket.updated_at = utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def _assign(db: Session, user: User, ticket: Ticket, agent_id: int) -> None:
    if user.role == Role.customer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Peran Anda tidak berhak")
    if user.role == Role.agent and agent_id != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Agent hanya boleh mengambil tiket untuk dirinya sendiri",
        )
    if ticket.status not in (TicketStatus.open, TicketStatus.in_progress):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Tiket yang sudah selesai tidak bisa di-assign"
        )
    if user.role == Role.agent and ticket.assigned_agent_id not in (None, user.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tiket sudah diambil agent lain")

    agent = db.scalar(
        select(User).where(
            User.id == agent_id,
            User.business_id == user.business_id,
            User.role == Role.agent,
        )
    )
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent tidak ditemukan")

    ticket.assigned_agent = agent
    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.in_progress


def _change_status(user: User, ticket: Ticket, new_status: TicketStatus) -> None:
    if user.role == Role.customer and new_status != TicketStatus.open:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Peran Anda tidak berhak")
    if ticket.status == TicketStatus.open and new_status == TicketStatus.in_progress:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ambil tiket dengan mengisi assigned_agent_id"
        )

    allowed_roles = STATUS_TRANSITIONS.get((ticket.status, new_status))
    if allowed_roles is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Perubahan status {ticket.status.value} -> {new_status.value} tidak diperbolehkan",
        )
    if user.role not in allowed_roles:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Peran Anda tidak berhak mengubah status ini"
        )
    if user.role == Role.agent and ticket.assigned_agent_id != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Hanya agent yang menangani tiket ini yang boleh mengubah statusnya",
        )

    ticket.status = new_status
    if new_status == TicketStatus.open:
        ticket.assigned_agent = None