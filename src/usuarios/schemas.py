from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.core.schemas import PaginatedResponse


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255, examples=["João Silva"])
    email: EmailStr = Field(..., examples=["joao@email.com"])
    idade: int = Field(..., ge=0, le=150, examples=[25])


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255, examples=["João Silva"])
    email: EmailStr | None = Field(None, examples=["joao@email.com"])
    idade: int | None = Field(None, ge=0, le=150, examples=[25])


class UsuarioResponse(UsuarioBase):
    id: UUID

    model_config = {"from_attributes": True}


UsuarioPaginatedResponse = PaginatedResponse[UsuarioResponse]
