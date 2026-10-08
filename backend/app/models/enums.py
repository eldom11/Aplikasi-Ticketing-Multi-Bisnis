import enum


class Role(str, enum.Enum):
    admin = "admin"
    agent = "agent"
    customer = "customer"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"