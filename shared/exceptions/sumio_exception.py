from typing import Optional


class SumioException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self):
        base = f"SumioException: {self.message}"
        if self.code is not None:
            base += f" (code: {self.code})"
        if self.details:
            base += f" | details: {self.details}"
        return base

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }

    __json__ = to_dict
