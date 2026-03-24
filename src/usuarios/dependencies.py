import redis.asyncio as redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_redis, get_session
from src.usuarios.repository import UsuarioRepository
from src.usuarios.service import UsuarioService


async def get_usuario_service(
    session: AsyncSession = Depends(get_session),
    cache: redis.Redis = Depends(get_redis),
) -> UsuarioService:
    repository = UsuarioRepository(session)
    return UsuarioService(repository, cache)
