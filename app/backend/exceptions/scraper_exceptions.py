from typing import Optional

from fastapi import HTTPException, status  # type: ignore


class ScheduleNotFound(HTTPException):
    def __init__(self, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {id} found",
        )


class TaskNotFound(HTTPException):
    def __init__(self, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with id {id} not found",
        )


class TaskAlreadyExisting(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A task named {name} already exists",
        )


class CityNotFound(HTTPException):
    def __init__(self, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {id} not found",
        )


class SiteNotFound(HTTPException):
    def __init__(self, id: Optional[int] = None, name: Optional[str] = None):
        if id is not None:
            detail = f"Site with id {id} not found"
        elif name is not None:
            detail = f"Site named '{name}' not found"
        else:
            detail = "No site found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class StationNotFound(HTTPException):
    def __init__(self, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {id} not found",
        )


class StationsNotFoundByCity(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stations found in this city",
        )
