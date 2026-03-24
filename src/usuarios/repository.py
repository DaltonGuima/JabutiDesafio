from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.usuarios.models import Usuario
from src.usuarios.schemas import UsuarioCreate, UsuarioUpdate


class UsuarioRepository:
    """Camada de acesso a dados — Single Responsibility: apenas operações de banco."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self, *, limit: int, offset: int) -> list[Usuario]:
        query = select(Usuario).limit(limit).offset(offset).order_by(Usuario.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        query = select(func.count()).select_from(Usuario)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        return await self._session.get(Usuario, usuario_id)

    async def get_by_email(self, email: str) -> Usuario | None:
        query = select(Usuario).where(Usuario.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: UsuarioCreate) -> Usuario:
        usuario = Usuario(**data.model_dump())
        self._session.add(usuario)
        await self._session.flush()
        await self._session.refresh(usuario)
        return usuario

    async def update(self, usuario: Usuario, data: UsuarioUpdate) -> Usuario:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(usuario, field, value)
        await self._session.flush()
        await self._session.refresh(usuario)
        return usuario

    async def delete(self, usuario: Usuario) -> None:
        await self._session.delete(usuario)
        await self._session.flush()
