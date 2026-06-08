from typing import Any, Optional, Union

from fastapi import HTTPException, status


class HTTP400(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)


class HTTP401(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers)


class HTTP402(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail, headers=headers)


class HTTP403(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)


class HTTP404(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class HTTP409(HTTPException):
    # ``detail`` is widened to also accept a dict so callers can return structured context
    # alongside the message (e.g. the id of a conflicting row). FastAPI serialises dicts
    # straight into ``{"detail": {...}}`` so string-detail consumers are unaffected.
    def __init__(self, detail: Union[str, dict[str, Any]], headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)


class HTTP422(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail, headers=headers)


class HTTP429(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail, headers=headers)


class HTTP500(HTTPException):
    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail, headers=headers)
