from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.usuarios.dependencies import get_usuario_service
from src.usuarios.schemas import (
    UsuarioPaginatedResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from src.usuarios.service import UsuarioService

router = APIRouter()


@router.get(
    "",
    response_model=UsuarioPaginatedResponse,
    summary="Listar todos os usuários",
    description="Retorna lista paginada de usuários.",
)
async def listar_usuarios(
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginação"),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioPaginatedResponse:
    return await service.get_all(limit=limit, offset=offset)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Buscar usuário por ID",
    description="Retorna os detalhes de um usuário específico.",
)
async def buscar_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.get_by_id(usuario_id)


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
    description="Cria um novo usuário com nome, email e idade.",
)
async def criar_usuario(
    data: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.create(data)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualizar usuário",
    description="Atualiza os dados de um usuário existente.",
)
async def atualizar_usuario(
    usuario_id: UUID,
    data: UsuarioUpdate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.update(usuario_id, data)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover usuário",
    description="Remove um usuário pelo ID.",
)
async def remover_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> None:
    await service.delete(usuario_id)
