from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models import User
from app.models.enums import Role
from app.schemas.user import UserCreate, UserOut
from app.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    admin: User = Depends(require_role(Role.admin)),
    db: Session = Depends(get_db),
):
    return users_service.list_users(db, admin)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    admin: User = Depends(require_role(Role.admin)),
    db: Session = Depends(get_db),
):
    return users_service.create_user(db, admin, data)