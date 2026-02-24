from fastapi import HTTPException, status  # type: ignore


class CitiesNotFoundException(HTTPException):
    def __init__(self, missing_ids):
        super().__init__(
            status_code=400,
            detail={
                "error": "Some cities not found",
                "missing_ids": list(missing_ids),
            },
        )


class SitesNotFoundException(HTTPException):
    def __init__(self, missing_ids):
        super().__init__(
            status_code=400,
            detail={
                "error": "Some sites not found",
                "missing_ids": list(missing_ids),
            },
        )


class FiltersPresetNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="No filter preset found")


class DuplicatePresetNameException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400, detail="A filter preset with this name already exists"
        )
