from fastapi import HTTPException, status


class UsuarioNaoEncontrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )


class EmailJaCadastrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )
