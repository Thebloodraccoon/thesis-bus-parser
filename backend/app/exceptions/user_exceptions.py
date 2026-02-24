from typing import Optional  # type: ignore
from fastapi import HTTPException, status  # type: ignore


class UserNotFoundException(HTTPException):
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        detail = "Пользователь не найден."

        if user_id:
            detail = f"Пользователь с ID {user_id} не найден."

        if email:
            detail = f"Пользователь с email {email} не найден."

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsException(HTTPException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с email {email} уже существует.",
        )


class InvalidRoleException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимая роль: {message}",
        )
