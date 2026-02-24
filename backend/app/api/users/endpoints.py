from typing import List, cast, Literal

from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.app.api.auth.utils import get_current_user, admin_only
from backend.app.api.users.schemas import UserResponse, UserCreate, UserUpdate
from backend.app.api.users.utils import CRUDUser
from backend.app.models.users import User
from backend.app.settings import settings

router = APIRouter()
crud_user = CRUDUser(User)


@router.get("/current", response_model=UserResponse)
def get_current_user_info(current_user_info: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user_info.id,
        email=current_user_info.email,
        role=cast(
            Literal["admin", "analytic", "user"], current_user_info.role
        ),
        created_at=current_user_info.created_at,
        updated_at=current_user_info.updated_at,
        last_login=current_user_info.last_login,
    )


@router.post("/invite-user", response_model=UserResponse)
async def invite_user(
    request: UserCreate,
    db: Session = Depends(settings.get_db),
    _: User = Depends(admin_only),
):
    return await crud_user.create_user(request, db)


@router.get("/list", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(settings.get_db),
    _: User = Depends(admin_only),
):
    return crud_user.get_all_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(settings.get_db),
    _: User = Depends(admin_only),
):
    return crud_user.get_user_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(settings.get_db),
    _: User = Depends(admin_only),
):
    user = crud_user.update_user(db, user_id, updates.model_dump(exclude_unset=True))
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(settings.get_db),
    _: User = Depends(admin_only),
):
    crud_user.delete_user(db, user_id)
