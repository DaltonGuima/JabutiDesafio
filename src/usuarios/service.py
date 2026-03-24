from uuid import UUID

import redis.asyncio as redis

from src.core.config import settings
from src.usuarios.exceptions import EmailJaCadastrado, UsuarioNaoEncontrado
from src.usuarios.repository import UsuarioRepository
from src.usuarios.schemas import (
    UsuarioPaginatedResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)

CACHE_KEY_ALL = "usuarios:all"
CACHE_KEY_DETAIL = "usuarios:detail:{id}"


class UsuarioService:
    """Camada de regras de negócio — orquestra repository + cache."""

    def __init__(self, repository: UsuarioRepository, cache: redis.Redis) -> None:
        self._repository = repository
        self._cache = cache
        self._ttl = settings.REDIS_CACHE_TTL

    async def get_all(self, *, limit: int, offset: int) -> UsuarioPaginatedResponse:
        cache_key = f"{CACHE_KEY_ALL}:limit={limit}:offset={offset}"
        cached = await self._cache.get(cache_key)
        if cached:
            return UsuarioPaginatedResponse.model_validate_json(cached)

        usuarios = await self._repository.get_all(limit=limit, offset=offset)
        total = await self._repository.count()

        response = UsuarioPaginatedResponse(
            items=[UsuarioResponse.model_validate(u) for u in usuarios],
            total=total,
            limit=limit,
            offset=offset,
        )
        await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)
        return response

    async def get_by_id(self, usuario_id: UUID) -> UsuarioResponse:
        cache_key = CACHE_KEY_DETAIL.format(id=usuario_id)
        cached = await self._cache.get(cache_key)
        if cached:
            return UsuarioResponse.model_validate_json(cached)

        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        response = UsuarioResponse.model_validate(usuario)
        await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)
        return response

    async def create(self, data: UsuarioCreate) -> UsuarioResponse:
        existing = await self._repository.get_by_email(data.email)
        if existing:
            raise EmailJaCadastrado()

        usuario = await self._repository.create(data)
        await self._invalidate_cache()
        return UsuarioResponse.model_validate(usuario)

    async def update(self, usuario_id: UUID, data: UsuarioUpdate) -> UsuarioResponse:
        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        if data.email and data.email != usuario.email:
            existing = await self._repository.get_by_email(data.email)
            if existing:
                raise EmailJaCadastrado()

        updated = await self._repository.update(usuario, data)
        await self._invalidate_cache(usuario_id)
        return UsuarioResponse.model_validate(updated)

    async def delete(self, usuario_id: UUID) -> None:
        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        await self._repository.delete(usuario)
        await self._invalidate_cache(usuario_id)

    async def _invalidate_cache(self, usuario_id: UUID | None = None) -> None:
        """Invalida cache de listagem e, se informado, do detalhe do usuário."""
        # Remove todas as chaves de listagem paginada
        async for key in self._cache.scan_iter(f"{CACHE_KEY_ALL}:*"):
            await self._cache.delete(key)

        # Remove cache do detalhe específico
        if usuario_id:
            await self._cache.delete(CACHE_KEY_DETAIL.format(id=usuario_id))
