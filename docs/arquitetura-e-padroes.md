# Arquitetura e Padrões do Projeto

## Visão Geral

O **Desafio Jabuti** é uma API REST CRUD de usuários construída com **FastAPI**, **PostgreSQL** e **Redis**. A aplicação segue princípios **SOLID**, **Clean Architecture** e padrões amplamente adotados no ecossistema Python/FastAPI.

---

## Estrutura de Pastas

```
src/
├── main.py                  # Ponto de entrada da aplicação FastAPI
├── __init__.py
├── core/                    # Infraestrutura compartilhada (cross-cutting)
│   ├── config.py            # Configurações centralizadas (pydantic-settings)
│   ├── database.py          # Engine + Session Factory do SQLAlchemy
│   ├── redis.py             # Cliente Redis async
│   ├── schemas.py           # Schemas genéricos reutilizáveis
│   └── dependencies.py      # Providers de DI globais (session, redis)
└── usuarios/                # Domínio "Usuários" (módulo de negócio)
    ├── models.py            # Modelo SQLAlchemy (tabela no banco)
    ├── schemas.py           # Schemas Pydantic (DTOs de entrada/saída)
    ├── exceptions.py        # Exceções HTTP de domínio
    ├── repository.py        # Acesso a dados (queries SQL)
    ├── service.py           # Regras de negócio + orquestração de cache
    ├── router.py            # Endpoints HTTP (controller)
    └── dependencies.py      # Composição de DI do módulo
```

### Por que essa estrutura?

- **`core/`** agrupa tudo que é **infraestrutura**: banco, cache, configuração. Se amanhã tiver um módulo `produtos/`, ele reutiliza `core/` sem duplicar nada.
- **`usuarios/`** é um **módulo de domínio** isolado. Cada domínio tem seus próprios models, schemas, repository, service e router. Isso é o padrão recomendado por projetos de referência como [Netflix Dispatch](https://github.com/Netflix/dispatch) e [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template).

---

## Camadas da Arquitetura

A aplicação segue uma arquitetura em camadas inspirada em Clean Architecture:

```
Request HTTP
     │
     ▼
┌──────────┐
│  Router   │  ← Recebe request, valida path/query params, retorna response
│ (router.py)│
└──────────┘
     │
     ▼
┌──────────┐
│  Service  │  ← Regras de negócio, orquestra Repository + Cache
│(service.py)│
└──────────┘
     │          ┌───────┐
     ├─────────►│ Cache  │  (Redis — leitura/escrita de cache)
     │          └───────┘
     ▼
┌──────────┐
│Repository │  ← Acesso a dados, queries SQL via SQLAlchemy
│(repository│
│   .py)    │
└──────────┘
     │
     ▼
┌──────────┐
│ Database  │  (PostgreSQL)
└──────────┘
```

### Responsabilidades de cada camada

| Camada | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **Router** | `router.py` | Define endpoints HTTP, valida parâmetros de entrada via Pydantic, delega para Service |
| **Service** | `service.py` | Contém regras de negócio (ex: "email deve ser único"), orquestra chamadas ao Repository e ao Cache |
| **Repository** | `repository.py` | Opera exclusivamente sobre o banco de dados. Executa queries SQL via SQLAlchemy |
| **Models** | `models.py` | Define a estrutura das tabelas no banco (ORM) |
| **Schemas** | `schemas.py` | Define contratos de entrada/saída (DTOs) usando Pydantic |

---

## Princípios SOLID Aplicados

### S — Single Responsibility (Responsabilidade Única)

Cada classe tem **uma única razão para mudar**:

- `UsuarioRepository` → só muda se a forma de acessar dados mudar
- `UsuarioService` → só muda se regras de negócio mudarem
- `router.py` → só muda se contratos HTTP mudarem

### O — Open/Closed (Aberto/Fechado)

- O `PaginatedResponse[T]` é **genérico** — aceita qualquer tipo sem ser modificado:

```python
# core/schemas.py
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

# usuarios/schemas.py — apenas cria um alias, sem modificar o original
UsuarioPaginatedResponse = PaginatedResponse[UsuarioResponse]
```

### L — Liskov Substitution (Substituição de Liskov)

- As exceções `UsuarioNaoEncontrado` e `EmailJaCadastrado` herdam de `HTTPException` e podem ser usadas em qualquer lugar que espera uma `HTTPException`.

### I — Interface Segregation (Segregação de Interface)

- O Router depende apenas do `UsuarioService`, não conhece Repository nem Redis.
- O Repository recebe apenas `AsyncSession`, não conhece Redis nem schemas de resposta.

### D — Dependency Inversion (Inversão de Dependência)

- Nenhuma camada instancia suas próprias dependências. Tudo é **injetado via `Depends()`** do FastAPI:

```python
# O Router recebe o Service via injeção
async def criar_usuario(
    data: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),  # ← injetado
) -> UsuarioResponse:
    return await service.create(data)
```

```python
# O Service recebe Repository e Cache via construtor
class UsuarioService:
    def __init__(self, repository: UsuarioRepository, cache: redis.Redis) -> None:
        self._repository = repository
        self._cache = cache
```

---

## Injeção de Dependência (Depends)

O FastAPI usa a função `Depends()` para montar a **árvore de dependências** automaticamente:

```
get_usuario_service()          ← compõe o Service
  ├── get_session()            ← fornece AsyncSession do SQLAlchemy
  │     └── async_session_factory()  ← cria a session
  └── get_redis()              ← fornece o cliente Redis
```

No código:

```python
# usuarios/dependencies.py
async def get_usuario_service(
    session: AsyncSession = Depends(get_session),   # FastAPI resolve isso primeiro
    cache: redis.Redis = Depends(get_redis),         # E isso também
) -> UsuarioService:
    repository = UsuarioRepository(session)           # Compõe o Repository
    return UsuarioService(repository, cache)          # Compõe o Service
```

- `get_session()` é um **AsyncGenerator** que faz `yield session`, commit automático e rollback em caso de erro.
- `get_redis()` retorna o singleton do cliente Redis.

---

## Tratamento de Exceções

### Exceções de Domínio

Em vez de espalhar `raise HTTPException(status_code=404, ...)` pelo código, criamos **exceções semânticas**:

```python
# usuarios/exceptions.py
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
```

### Por que Exceções Customizadas?

1. **Legibilidade**: `raise UsuarioNaoEncontrado()` é mais claro que `raise HTTPException(status_code=404, detail="...")`
2. **Centralização**: Se o texto ou status mudar, muda em um único lugar
3. **Reutilização**: Podem ser usadas em qualquer service/router sem repetir strings

### Validação Automática pelo Pydantic

O Pydantic valida automaticamente os dados de entrada nos schemas. Se alguém enviar um body inválido, o FastAPI retorna `422 Unprocessable Entity` com detalhes do erro — sem precisar de código manual:

```python
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr                                       # ← valida formato de email
    idade: int = Field(..., ge=0, le=150)                 # ← valida range
```

---

## Async/Await

Toda a aplicação é **assíncrona**:

- **SQLAlchemy Async** com `asyncpg` (driver PostgreSQL assíncrono)
- **Redis Async** com `redis.asyncio`
- **Endpoints async** — FastAPI roda tudo no event loop

Isso significa que enquanto uma query está esperando resposta do banco, o servidor pode atender outras requisições. É o modelo de concorrência do Python moderno.

---

## Configuração Centralizada

Usamos `pydantic-settings` para carregar configurações do **ambiente** (variáveis de ambiente do Docker):

```python
class Settings(BaseSettings):
    DATABASE_URL: str             # ← vem do docker-compose.yml
    REDIS_URL: str                # ← vem do docker-compose.yml
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    REDIS_CACHE_TTL: int = 300    # 5 minutos — pode ser sobrescrita por env var

    class Config:
        env_file = ".env"         # fallback para arquivo local
```

- Em **produção**, basta setar variáveis de ambiente sem tocar no código.
- O `ENVIRONMENT` controla comportamentos como `echo=True` no SQL (só em dev) e exposição do OpenAPI (desabilitado em prod).

---

## Lifespan (Ciclo de Vida)

O FastAPI permite definir lógica de **startup** e **shutdown** via `@asynccontextmanager`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: cria tabelas se não existirem
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # SHUTDOWN: fecha conexões limpamente
    await redis_client.close()
    await engine.dispose()
```

- No **startup**: cria as tabelas automaticamente (útil em dev, em prod usaria Alembic migrations).
- No **shutdown**: fecha conexões com Redis e PostgreSQL para não vazar recursos.

---

## Middleware CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,    # ["http://localhost:8000", "http://fastapi-app:8000"]
    allow_credentials=False,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
```

- **CORS** (Cross-Origin Resource Sharing) controla quais origens podem acessar a API.
- Configurado de forma restritiva: apenas as origens dos próprios containers são permitidas.
- Métodos e headers são configuráveis via `Settings`.

---

## Resumo: Fluxo Completo de uma Requisição

Exemplo: `POST /usuarios` com body `{"nome": "João", "email": "joao@email.com", "idade": 25}`

1. **FastAPI** recebe o request e valida o body contra `UsuarioCreate` (Pydantic)
2. **Depends** resolve a árvore: `get_session()` → abre session, `get_redis()` → retorna client
3. `get_usuario_service()` compõe `UsuarioRepository(session)` e `UsuarioService(repo, cache)`
4. **Router** chama `service.create(data)`
5. **Service** verifica se email já existe via `repository.get_by_email()`
6. Se não existe, **Repository** faz `session.add(usuario)` + `flush()` + `refresh()`
7. **Service** invalida o cache Redis (remove chaves de listagem)
8. **Response** é serializado via `UsuarioResponse` (Pydantic) e retornado com status 201
9. **Depends** faz cleanup: `session.commit()` (ou rollback se houve erro)
