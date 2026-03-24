from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico de paginação — reutilizável por qualquer domínio."""

    items: list[T]
    total: int
    limit: int
    offset: int
