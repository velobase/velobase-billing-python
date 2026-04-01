from __future__ import annotations


class VelobaseError(Exception):
    """Base error for all Velobase API errors."""

    def __init__(self, message: str, status: int, type: str) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.type = type

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status={self.status})"


class AuthenticationError(VelobaseError):
    """Raised on 401 responses."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 401, "auth_error")


class ValidationError(VelobaseError):
    """Raised on 400 responses."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 400, "validation_error")


class NotFoundError(VelobaseError):
    """Raised on 404 responses."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 404, "not_found")


class ConflictError(VelobaseError):
    """Raised on 409 responses."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 409, "conflict")


class InternalError(VelobaseError):
    """Raised on 500 responses."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 500, "server_error")
