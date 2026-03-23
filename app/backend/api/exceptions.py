from fastapi import HTTPException, status


class AppException(HTTPException):
    """The base class for all domain exceptions in the application."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "An error occurred"

    def __init__(self, detail: str | dict | None = None):
        super().__init__(
            status_code=self.__class__.status_code,
            detail=detail or self.__class__.detail,
        )


class InvalidCredentialsException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email address or password"

    def __init__(self):
        HTTPException.__init__(
            self,
            status_code=self.status_code,
            headers={"WWW-Authenticate": "Bearer"},
            detail=self.detail,
        )


class InvalidCodeException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid two-step verification code"

    def __init__(self):
        HTTPException.__init__(
            self,
            status_code=self.status_code,
            headers={"WWW-Authenticate": "Bearer"},
            detail=self.detail,
        )


class InvalidEmailException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid email address"


class AdminAccessException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Only administrators have access"


class AnalyticsOrAdminAccessException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Only analytics or administrators have access"


class TokenBlacklistedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "The token was blacklisted"

    def __init__(self):
        HTTPException.__init__(
            self,
            status_code=self.status_code,
            headers={"WWW-Authenticate": "Bearer"},
            detail=self.detail,
        )


class InvalidTokenException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Credentials could not be verified"

    def __init__(self):
        HTTPException.__init__(
            self,
            status_code=self.status_code,
            headers={"WWW-Authenticate": "Bearer"},
            detail=self.detail,
        )


class UserNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, user_id: int | None = None, email: str | None = None):
        if user_id:
            detail = f"User with ID {user_id} not found."
        elif email:
            detail = f"User with email {email} not found."
        else:
            detail = "User not found."
        super().__init__(detail)


class UserAlreadyExistsException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, email: str):
        super().__init__(f"A user with email {email} already exists.")


class NotFoundException(AppException):
    """The base class for errors is "not found"."""

    status_code = status.HTTP_404_NOT_FOUND


class SiteNotFoundException(NotFoundException):
    def __init__(self, id: int | None = None, name: str | None = None):
        if id is not None:
            detail = f"Site with id {id} not found"
        elif name is not None:
            detail = f"Site named '{name}' not found"
        else:
            detail = "No site found"
        super().__init__(detail)


class CityNotFoundException(NotFoundException):
    def __init__(self, id: int):
        super().__init__(f"City with id {id} not found")


class StationNotFoundException(NotFoundException):
    def __init__(self, id: int):
        super().__init__(f"Station with id {id} not found")


class StationsNotFoundByCityException(NotFoundException):
    def __init__(self):
        super().__init__("No stations found in this city")


class ScheduleNotFoundException(NotFoundException):
    def __init__(self, id: int):
        super().__init__(f"Schedule with id {id} not found")


class TaskNotFoundException(NotFoundException):
    def __init__(self, id: int):
        super().__init__(f"Task with id {id} not found")


class TaskAlreadyExistsException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, name: str):
        super().__init__(f"A task named {name} already exists")


class CitiesNotFoundException(AppException):
    def __init__(self, missing_ids):
        super().__init__(
            {"error": "Some cities not found", "missing_ids": list(missing_ids)}
        )


class SitesNotFoundException(AppException):
    def __init__(self, missing_ids):
        super().__init__(
            {"error": "Some sites not found", "missing_ids": list(missing_ids)}
        )


class FiltersPresetNotFoundException(AppException):
    detail = "No filter preset found"


class DuplicatePresetNameException(AppException):
    detail = "A filter preset with this name already exists"
