# Python para Quem Vem de Outra Linguagem — Sintaxe Linha por Linha

Guia completo de **cada linha de código** do projeto, com foco na sintaxe do Python.

> **Convenção deste guia**: `←` indica um comentário explicativo que NÃO faz parte do código.

---

## Índice

1. [Conceitos Básicos da Sintaxe Python](#1-conceitos-básicos-da-sintaxe-python)
2. [config.py — Configuração](#2-configpy--configuração)
3. [database.py — Banco de Dados](#3-databasepy--banco-de-dados)
4. [redis.py — Cliente Cache](#4-redispy--cliente-cache)
5. [schemas.py (core) — Schema Genérico](#5-schemaspy-core--schema-genérico)
6. [dependencies.py (core) — Injeção de Dependência](#6-dependenciespy-core--injeção-de-dependência)
7. [models.py — Modelo do Banco](#7-modelspy--modelo-do-banco)
8. [schemas.py (usuarios) — DTOs](#8-schemaspy-usuarios--dtos)
9. [exceptions.py — Exceções Customizadas](#9-exceptionspy--exceções-customizadas)
10. [repository.py — Acesso a Dados](#10-repositorypy--acesso-a-dados)
11. [service.py — Regras de Negócio](#11-servicepy--regras-de-negócio)
12. [router.py — Endpoints HTTP](#12-routerpy--endpoints-http)
13. [dependencies.py (usuarios) — Composição](#13-dependenciespy-usuarios--composição)
14. [main.py — Ponto de Entrada](#14-mainpy--ponto-de-entrada)

---

## 1. Conceitos Básicos da Sintaxe Python

Antes de ler o código, entenda estas diferenças fundamentais:

### Indentação define blocos (não chaves `{}`)

```python
# Python — indentação OBRIGATÓRIA (4 espaços)
if idade > 18:
    print("maior")       # ← dentro do if
    print("de idade")    # ← ainda dentro do if
print("sempre executa")  # ← fora do if (voltou um nível)

# Java — chaves definem o bloco
# if (idade > 18) {
#     System.out.println("maior");
# }
```

### Sem ponto-e-vírgula `;`

Cada linha é uma instrução. Não precisa de `;` no final.

### Sem declaração de tipo obrigatória

```python
nome = "João"       # Python descobre que é string sozinho
idade = 25          # Python descobre que é int
```

Mas podemos usar **type hints** (dicas de tipo) opcionais:

```python
nome: str = "João"  # ← : str é uma DICA, não obrigação
idade: int = 25     # ← Python não impede usar nome = 123 depois
```

### `self` ao invés de `this`

```python
class Pessoa:
    def __init__(self, nome):  # ← self é obrigatório como 1º parâmetro
        self.nome = nome       # ← equivale a this.nome = nome em Java
```

### f-strings (interpolação)

```python
nome = "João"
print(f"Olá, {nome}!")           # ← f"..." permite {variavel} dentro da string
# Resultado: Olá, João!

# Em Java seria: "Olá, " + nome + "!" ou String.format("Olá, %s!", nome)
```

---

## 2. config.py — Configuração

```python
from enum import StrEnum
```

- `from X import Y` = importa **apenas** `Y` do módulo `X`
- `enum` é um módulo da biblioteca padrão do Python
- `StrEnum` é uma classe que combina enum + string (cada valor é uma string)

```python
from pydantic_settings import BaseSettings
```

- Importa `BaseSettings` da biblioteca `pydantic_settings` (instalada via pip)
- `BaseSettings` lê variáveis de ambiente automaticamente

```python
class Environment(StrEnum):
```

- `class NomeDaClasse(ClassePai):` = define uma classe que **herda** de `ClassePai`
- `Environment` herda de `StrEnum` → cada membro é uma string

```python
    DEVELOPMENT = "development"
    PRODUCTION = "production"
```

- Membros do enum — `Environment.DEVELOPMENT` tem o valor `"development"`
- A indentação (4 espaços) indica que estão **dentro** da classe

```python
class Settings(BaseSettings):
```

- Classe `Settings` herda de `BaseSettings` → ganha poderes de leitura de env vars

```python
    DATABASE_URL: str
```

- `: str` = **type annotation** (anotação de tipo) — declara que `DATABASE_URL` é uma string
- Como não tem `= valor`, é **obrigatório** — se não vier da env var, dá erro ao iniciar

```python
    REDIS_URL: str
```

- Mesmo padrão — variável obrigatória do tipo string

```python
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
```

- `: Environment` = tipo é o enum que criamos acima
- `= Environment.DEVELOPMENT` = **valor padrão** — se não for informada, usa "development"

```python
    REDIS_CACHE_TTL: int = 300  # 5 minutos
```

- `: int` = tipo inteiro
- `= 300` = padrão de 300 segundos
- `# 5 minutos` = **comentário** — tudo depois de `#` na mesma linha é ignorado pelo Python

```python
    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://fastapi-app:8000",
    ]
```

- `list[str]` = tipo é uma **lista de strings** (equivalente a `List<String>` em Java)
- `[ ]` = literal de lista em Python
- A vírgula final após o último item (`",",`) é **opcional** mas boa prática em Python (facilita diffs no git)

```python
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS: list[str] = ["Content-Type", "Accept"]
```

- Mesma sintaxe: listas de strings com valores padrão

```python
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

- **Classe interna** (inner class) — `Config` dentro de `Settings`
- é uma convenção do Pydantic: configura de onde ler as variáveis
- `env_file = ".env"` = se existir arquivo `.env` na raiz, lê as variáveis dele

```python
settings = Settings()
```

- Cria uma **instância** da classe `Settings`
- `Settings()` = chama o construtor (como `new Settings()` em Java)
- Neste momento, o Pydantic lê as variáveis de ambiente e preenche todos os campos
- `settings` é uma variável **no nível do módulo** = acessível por quem importar este arquivo

---

## 3. database.py — Banco de Dados

```python
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
```

- Importa múltiplos itens de um módulo com vírgula: `import A, B, C`
- `sqlalchemy.ext.asyncio` = submódulo (pasta dentro de pasta) do SQLAlchemy

```python
from src.core.config import settings
```

- `src.core.config` = caminho do módulo (equivale a `src/core/config.py`)
- O `.` é o separador de pacotes em Python (como `/` nas pastas)

```python
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
```

- `NOME_MAIUSCULO` = convenção Python para **constante** (não é imposto, é acordo entre devs)
- `{ }` = literal de **dicionário** (equivalente a `Map<String, String>` ou `HashMap` em Java)
- `"chave": "valor"` = par chave-valor
- `%(nome)s` = sintaxe do Python para interpolação estilo `printf` (`%s` = string)

```python
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)
```

- `naming_convention=` é um **keyword argument** (argumento nomeado)
- Python permite passar argumentos **pelo nome**: `funcao(nome="valor")`
- Em Java seria: não existe equivalente direto; usaria builder pattern

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
)
```

- `settings.DATABASE_URL` = acesso a atributo do objeto (como Java)
- `settings.ENVIRONMENT == "development"` = comparação que retorna `True` ou `False`
- `echo=True/False` = keyword argument — se `True`, imprime todas as queries SQL no console
- Note: `==` é comparação, `=` é atribuição (como Java)

```python
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

- `class_=AsyncSession` = o `_` no final de `class_` é porque `class` é **palavra reservada** em Python (não pode ser usada como nome de parâmetro)
- `expire_on_commit=False` = não invalida objetos carregados após commit

---

## 4. redis.py — Cliente Cache

```python
import redis.asyncio as redis
```

- `import X as Y` = importa o módulo `X` mas **renomeia** para `Y` no código
- `redis.asyncio` é o submódulo assíncrono da biblioteca redis
- Após essa linha, usamos `redis.` no lugar de `redis.asyncio.`

```python
from src.core.config import settings
```

- Já vimos: importa a instância `settings` do nosso arquivo de config

```python
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)
```

- `redis.from_url()` = chama uma **factory function** (método de fábrica) que cria o cliente
- `decode_responses=True` = retorna `str` ao invés de `bytes` (b"texto")
- `redis_client` = variável no nível do módulo (singleton)

---

## 5. schemas.py (core) — Schema Genérico

```python
from typing import Generic, TypeVar
```

- `typing` = módulo padrão do Python para tipos avançados
- `Generic` = permite criar classes genéricas (como `<T>` em Java)
- `TypeVar` = cria uma "variável de tipo" (o T dos generics)

```python
from pydantic import BaseModel
```

- `BaseModel` = classe base do Pydantic — valida dados automaticamente

```python
T = TypeVar("T")
```

- Cria a variável de tipo `T` — equivalente a declarar `<T>` em Java
- A string `"T"` é o nome exibido em mensagens de erro

```python
class PaginatedResponse(BaseModel, Generic[T]):
```

- **Herança múltipla**: `PaginatedResponse` herda de **duas** classes: `BaseModel` E `Generic[T]`
- Python permite herança múltipla (Java não — Java usa interfaces)
- `Generic[T]` = esta classe aceita um tipo genérico (será substituído depois)

```python
    """Schema genérico de paginação — reutilizável por qualquer domínio."""
```

- **Docstring** = string entre `"""..."""` logo após a declaração da classe/função
- É a documentação oficial — acessível via `help(PaginatedResponse)` ou IDEs

```python
    items: list[T]
    total: int
    limit: int
    offset: int
```

- Campos da classe — `list[T]` significa "lista do tipo que for escolhido"
- Quando alguém fizer `PaginatedResponse[UsuarioResponse]`, `T` vira `UsuarioResponse`
- `items` vira `list[UsuarioResponse]`

---

## 6. dependencies.py (core) — Injeção de Dependência

```python
from collections.abc import AsyncGenerator
```

- `collections.abc` = módulo de tipos abstratos (Abstract Base Classes)
- `AsyncGenerator` = tipo que representa um gerador assíncrono (função com `yield`)

```python
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
```

- Já vistos: importações com renomeação e de submódulos

```python
from src.core.database import async_session_factory
from src.core.redis import redis_client
```

- Importa objetos específicos de nossos próprios módulos

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
```

- `async def` = define uma **função assíncrona** (coroutine)
- `def` sozinho seria uma função normal (síncrona)
- `get_session()` = nome da função (snake_case é o padrão Python, não camelCase)
- `-> AsyncGenerator[AsyncSession, None]` = **return type** (tipo de retorno)
  - `AsyncGenerator[TipoQueEntrega, TipoQueRecebe]`
  - Entrega `AsyncSession`, não recebe nada (`None`)

```python
    async with async_session_factory() as session:
```

- `async with X as Y:` = **gerenciador de contexto assíncrono**
  - Equivalente ao try-with-resources do Java: `try (var session = factory.create()) { ... }`
  - Garante que `session` será fechada ao sair do bloco (mesmo se der erro)
- `as session` = o objeto criado é chamado de `session`

```python
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- `try:` / `except:` = equivalente a `try` / `catch` em Java
- `yield session` = **pausa** a função e entrega `session` para quem chamou
  - É o que torna esta função um **generator** (explicado anteriormente)
- `await` = espera uma operação assíncrona terminar
  - Só pode ser usado dentro de `async def`
  - Equivalente conceitual ao `.get()` de um `CompletableFuture` em Java
- `except Exception:` = captura **qualquer** exceção (como `catch (Exception e)` em Java)
  - Python não especifica a variável se não for usá-la (em Java seria `catch (Exception e)`)
- `raise` = relança a exceção capturada (como `throw` sem argumento em Java)
  - `raise` sozinho = relança a mesma exceção do `except`

```python
async def get_redis() -> redis.Redis:
    return redis_client
```

- Função simples que retorna o singleton do redis
- `-> redis.Redis` = tipo de retorno é `redis.Redis`

---

## 7. models.py — Modelo do Banco

```python
import uuid
```

- Importa o **módulo inteiro** `uuid` (diferente de `from uuid import UUID`)
- Depois usamos `uuid.uuid4`, `uuid.UUID`

```python
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
```

- `sqlalchemy.dialects.postgresql` = tipos específicos do PostgreSQL
- `Mapped` = wrapper de tipo do SQLAlchemy 2.0 para anotações de tipo
- `mapped_column` = define uma coluna com configurações

```python
class Base(DeclarativeBase):
    pass
```

- `pass` = **"não faz nada"** — é o placeholder do Python
- Usado quando uma classe/função precisa de um corpo mas não tem lógica
- Em Java seria: `class Base extends DeclarativeBase { }` (corpo vazio)

```python
class Usuario(Base):
    __tablename__ = "usuario"
```

- Herda de `Base` (que herda de `DeclarativeBase` do SQLAlchemy)
- `__tablename__` = nome da tabela no banco de dados
- `__nome__` = atributo "dunder" (double underscore) — é uma convenção Python para atributos especiais/mágicos

```python
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
```

- `Mapped[uuid.UUID]` = anotação de tipo — esta coluna é um UUID do Python
- `mapped_column(...)` = configura a coluna no banco
- `UUID(as_uuid=True)` = tipo da coluna no PostgreSQL (UUID nativo)
- `primary_key=True` = é a chave primária
- `default=uuid.uuid4` = note que **NÃO tem `()`** — passa a **função** como referência, não o resultado
  - `uuid.uuid4` = referência à função (será chamada pelo SQLAlchemy quando precisar)
  - `uuid.uuid4()` = chamaria agora e todos teriam o MESMO UUID

```python
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    idade: Mapped[int] = mapped_column(nullable=False)
```

- `String(255)` = VARCHAR(255) no banco
- `nullable=False` = NOT NULL
- `unique=True` = UNIQUE constraint

```python
    def __repr__(self) -> str:
        return f"<Usuario(id={self.id}, nome={self.nome}, email={self.email})>"
```

- `__repr__` = método mágico — define como o objeto aparece no terminal/logs
  - Equivalente ao `toString()` do Java
- `def metodo(self)` = método de instância — `self` é sempre o 1º parâmetro
- `f"..."` = f-string com interpolação de variáveis

---

## 8. schemas.py (usuarios) — DTOs

```python
from uuid import UUID
```

- Importa **apenas** a classe `UUID` do módulo `uuid`

```python
from pydantic import BaseModel, EmailStr, Field
```

- `EmailStr` = tipo especial que valida formato de email
- `Field` = permite configurar validações e metadados de cada campo

```python
from src.core.schemas import PaginatedResponse
```

- Importa nosso schema genérico de paginação

```python
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255, examples=["João Silva"])
    email: EmailStr = Field(..., examples=["joao@email.com"])
    idade: int = Field(..., ge=0, le=150, examples=[25])
```

- `Field(...)` = configura validação do campo
- `...` (reticências literais) = em Python, `...` é o objeto `Ellipsis` — aqui significa **"obrigatório"**
  - É um singleton como `None`, `True`, `False`
  - O Pydantic interpreta como "este campo não tem valor padrão, deve ser informado"
- `min_length=1` = tamanho mínimo 1 (não aceita string vazia)
- `max_length=255` = tamanho máximo
- `ge=0` = "greater than or equal" ≥ 0
- `le=150` = "less than or equal" ≤ 150
- `examples=["João Silva"]` = exemplo que aparece no Swagger

```python
class UsuarioCreate(UsuarioBase):
    pass
```

- Herda **tudo** de `UsuarioBase` sem acrescentar nada
- Existe como classe separada para clareza semântica (é o DTO de criação)

```python
class UsuarioUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255, examples=["João Silva"])
    email: EmailStr | None = Field(None, examples=["joao@email.com"])
    idade: int | None = Field(None, ge=0, le=150, examples=[25])
```

- `str | None` = **Union type** — pode ser `str` OU `None` (nulo)
  - Equivalente a `Optional<String>` em Java
  - O `|` para tipos foi introduzido no Python 3.10
- `Field(None, ...)` = valor padrão é `None` — campo **opcional**
- Isso permite partial updates: enviar apenas `{"nome": "Novo Nome"}` sem os outros campos

```python
class UsuarioResponse(UsuarioBase):
    id: UUID
```

- Herda `nome`, `email`, `idade` de `UsuarioBase` e adiciona `id`

```python
    model_config = {"from_attributes": True}
```

- `model_config` = dicionário de configuração do Pydantic v2
- `"from_attributes": True` = permite criar este schema a partir de um objeto SQLAlchemy
  - Sem isso, `UsuarioResponse.model_validate(usuario_orm)` falharia
  - É o equivalente ao `orm_mode = True` do Pydantic v1

```python
UsuarioPaginatedResponse = PaginatedResponse[UsuarioResponse]
```

- **Alias de tipo** — cria um nome novo para `PaginatedResponse[UsuarioResponse]`
- `PaginatedResponse[UsuarioResponse]` = resolve o genérico `T` para `UsuarioResponse`
  - `items: list[T]` vira `items: list[UsuarioResponse]`
- É como `typedef` em C ou `type alias` em Kotlin

---

## 9. exceptions.py — Exceções Customizadas

```python
from fastapi import HTTPException, status
```

- `HTTPException` = exceção que o FastAPI converte em resposta HTTP automaticamente
- `status` = módulo com constantes de status HTTP (404, 409, etc.)

```python
class UsuarioNaoEncontrado(HTTPException):
    def __init__(self) -> None:
```

- `def __init__(self)` = **construtor** da classe (equivalente ao `public UsuarioNaoEncontrado()` em Java)
- `__init__` = método mágico chamado quando fazemos `UsuarioNaoEncontrado()`
- `-> None` = retorno do construtor é sempre `None` (construtores não retornam valor)

```python
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
```

- `super()` = referência à classe pai (`HTTPException`)
- `super().__init__(...)` = chama o construtor do pai (como `super(...)` em Java)
- `status.HTTP_404_NOT_FOUND` = constante com valor `404`

```python
class EmailJaCadastrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )
```

- Mesmo padrão: exceção customizada com status 409 e mensagem fixa

---

## 10. repository.py — Acesso a Dados

```python
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.usuarios.models import Usuario
from src.usuarios.schemas import UsuarioCreate, UsuarioUpdate
```

- Múltiplas importações — padrão já visto

```python
class UsuarioRepository:
    """Camada de acesso a dados — Single Responsibility: apenas operações de banco."""
```

- Docstring como primeira linha da classe

```python
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
```

- `self._session` = o `_` no início é **convenção** para "privado"
  - Python **não tem** `private` de verdade — é apenas acordo entre devs
  - `_nome` = "não mexa nisso de fora da classe" (warning)
  - `__nome` = name mangling (mais restritivo, raramente usado)

```python
    async def get_all(self, *, limit: int, offset: int) -> list[Usuario]:
```

- `*` sozinho nos parâmetros = tudo DEPOIS do `*` deve ser passado **por nome**
  - `get_all(limit=10, offset=0)` ✓
  - `get_all(10, 0)` ✗ (erro!)
  - Isso evita confusão na ordem dos argumentos
- `-> list[Usuario]` = retorna uma lista de objetos `Usuario`

```python
        query = select(Usuario).limit(limit).offset(offset).order_by(Usuario.nome)
```

- **Method chaining** (encadeamento) — cada `.metodo()` retorna o objeto para continuar
- `select(Usuario)` = `SELECT * FROM usuario`
- `.limit(limit)` = `LIMIT 10`
- `.offset(offset)` = `OFFSET 0`
- `.order_by(Usuario.nome)` = `ORDER BY nome`

```python
        result = await self._session.execute(query)
        return list(result.scalars().all())
```

- `await` = espera a query terminar (assíncrono)
- `result.scalars()` = extrai objetos do resultado (ao invés de tuplas)
- `.all()` = retorna todos como lista
- `list(...)` = converte para lista Python pura (garante o tipo)

```python
    async def count(self) -> int:
        query = select(func.count()).select_from(Usuario)
```

- `func.count()` = `COUNT(*)` em SQL
- `.select_from(Usuario)` = `FROM usuario`

```python
        result = await self._session.execute(query)
        return result.scalar_one()
```

- `scalar_one()` = retorna **um único valor** (o número do count)

```python
    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        return await self._session.get(Usuario, usuario_id)
```

- `.get(Classe, chave_primaria)` = busca por PK
- `-> Usuario | None` = pode retornar o objeto OU `None` se não encontrar

```python
    async def get_by_email(self, email: str) -> Usuario | None:
        query = select(Usuario).where(Usuario.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
```

- `.where(Usuario.email == email)` = `WHERE email = 'valor'`
  - O `==` aqui NÃO é comparação Python — o SQLAlchemy sobrecarrega o operador para gerar SQL
- `scalar_one_or_none()` = retorna o objeto ou `None` (erro se achar mais de 1)

```python
    async def create(self, data: UsuarioCreate) -> Usuario:
        usuario = Usuario(**data.model_dump())
```

- `data.model_dump()` = converte o Pydantic schema para dicionário
  - Ex: `{"nome": "João", "email": "joao@email.com", "idade": 25}`
- `**dicionario` = **unpacking** — espalha as chaves como argumentos nomeados:
  - `Usuario(**{"nome": "João", "email": "joao@email.com", "idade": 25})`
  - Vira: `Usuario(nome="João", email="joao@email.com", idade=25)`
  - É como `...spread` no JavaScript

```python
        self._session.add(usuario)
        await self._session.flush()
        await self._session.refresh(usuario)
        return usuario
```

- `.add(obj)` = marca para inserção (como `persist()` no JPA)
- `flush()` = envia o SQL para o banco **sem commit** (commit é feito pelo dependency)
- `refresh(obj)` = recarrega o objeto do banco (pega o UUID gerado, por exemplo)

```python
    async def update(self, usuario: Usuario, data: UsuarioUpdate) -> Usuario:
        update_data = data.model_dump(exclude_unset=True)
```

- `exclude_unset=True` = inclui **apenas** campos que foram enviados no body
  - Se o body foi `{"nome": "Novo"}`, retorna apenas `{"nome": "Novo"}`
  - Campos não enviados (email, idade) são excluídos — não sobrescreve com `None`

```python
        for field, value in update_data.items():
            setattr(usuario, field, value)
```

- `for chave, valor in dicionario.items():` = itera sobre pares do dicionário
  - `.items()` retorna pares `(chave, valor)`
  - **Destructuring**: `field, value` desmembra cada par
- `setattr(objeto, "atributo", valor)` = define um atributo dinamicamente
  - `setattr(usuario, "nome", "Novo")` equivale a `usuario.nome = "Novo"`
  - Porque o nome do campo é uma **string variável**, não podemos usar `usuario.nome` diretamente

```python
        await self._session.flush()
        await self._session.refresh(usuario)
        return usuario
```

- Mesma lógica do create: flush (sem commit) + refresh

```python
    async def delete(self, usuario: Usuario) -> None:
        await self._session.delete(usuario)
        await self._session.flush()
```

- `.delete(obj)` = marca para deleção
- `-> None` = não retorna nada (como `void` em Java)

---

## 11. service.py — Regras de Negócio

```python
CACHE_KEY_ALL = "usuarios:all"
CACHE_KEY_DETAIL = "usuarios:detail:{id}"
```

- Constantes de string (nível do módulo, fora de qualquer classe)
- `{id}` dentro da string NÃO é f-string (não tem `f` na frente) — é um placeholder para `.format()` depois

```python
class UsuarioService:
    """Camada de regras de negócio — orquestra repository + cache."""

    def __init__(self, repository: UsuarioRepository, cache: redis.Redis) -> None:
        self._repository = repository
        self._cache = cache
        self._ttl = settings.REDIS_CACHE_TTL
```

- Construtor recebe duas dependências e guarda como atributos privados (`_`)

```python
    async def get_all(self, *, limit: int, offset: int) -> UsuarioPaginatedResponse:
        cache_key = f"{CACHE_KEY_ALL}:limit={limit}:offset={offset}"
```

- f-string: `f"{variavel}"` interpolada
- Resultado: `"usuarios:all:limit=10:offset=0"`

```python
        cached = await self._cache.get(cache_key)
        if cached:
            return UsuarioPaginatedResponse.model_validate_json(cached)
```

- `if cached:` = em Python, `None`, `""`, `0`, `[]`, `False` são **falsy**
  - Se o Redis retornou `None` (miss), o `if` é falso → segue para o banco
  - Se retornou uma string JSON (hit), o `if` é verdadeiro → desserializa e retorna
- `model_validate_json(string)` = desserializa JSON para objeto Pydantic

```python
        response = UsuarioPaginatedResponse(
            items=[UsuarioResponse.model_validate(u) for u in usuarios],
            total=total,
            limit=limit,
            offset=offset,
        )
```

- `[expressao for item in lista]` = **list comprehension** — forma compacta de criar lista
  - Equivale a:

    ```python
    items = []
    for u in usuarios:
        items.append(UsuarioResponse.model_validate(u))
    ```

  - Em Java seria: `usuarios.stream().map(u -> UsuarioResponse.from(u)).toList()`

```python
        await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)
```

- `.model_dump_json()` = serializa o objeto Pydantic para string JSON
- `ex=self._ttl` = expire in seconds (TTL do cache)

```python
    async def get_by_id(self, usuario_id: UUID) -> UsuarioResponse:
        cache_key = CACHE_KEY_DETAIL.format(id=usuario_id)
        cached = await self._cache.get(cache_key)
        if cached:
            return UsuarioResponse.model_validate_json(cached)
```

- Mesma lógica cache-aside do `get_all`: tenta buscar no Redis primeiro
- `CACHE_KEY_DETAIL.format(id=usuario_id)` = monta chave `"usuarios:detail:abc-123"`

```python
        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        response = UsuarioResponse.model_validate(usuario)
        await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)
        return response
```

- Se não achou no cache, busca no banco
- Se não existe no banco (`not usuario`), lança exceção 404
- Se existe, converte para DTO, salva no cache com TTL e retorna

```python
    async def create(self, data: UsuarioCreate) -> UsuarioResponse:
        existing = await self._repository.get_by_email(data.email)
        if existing:
            raise EmailJaCadastrado()
```

- Antes de criar, verifica se o email já existe no banco
- `if existing:` = se achou alguém com esse email, lança exceção 409

```python
        usuario = await self._repository.create(data)
        await self._invalidate_cache()
        return UsuarioResponse.model_validate(usuario)
```

- Cria no banco, **invalida todo o cache de listagem** (pois mudou), retorna o novo usuário
- Note: `self._invalidate_cache()` sem `usuario_id` — pois é um usuário novo, não tinha cache de detalhe

```python
    async def update(self, usuario_id: UUID, data: UsuarioUpdate) -> UsuarioResponse:
        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()
```

- `if not X:` = verificação se é `None`/falsy (como `if (usuario == null)` em Java)
- `raise` = lança exceção (como `throw` em Java)
- `UsuarioNaoEncontrado()` = instancia a exceção (chama o construtor)

```python
        if data.email and data.email != usuario.email:
```

- `and` = operador lógico E (como `&&` em Java)
- Python usa palavras: `and`, `or`, `not` (não `&&`, `||`, `!`)

```python
            existing = await self._repository.get_by_email(data.email)
            if existing:
                raise EmailJaCadastrado()
```

- **Validação condicional**: só verifica unicidade do email se ele foi informado E é diferente do atual
- Evita conflito falso quando o usuário mantém o mesmo email

```python
        updated = await self._repository.update(usuario, data)
        await self._invalidate_cache(usuario_id)
        return UsuarioResponse.model_validate(updated)
```

- Atualiza no banco, invalida cache (de listagem + detalhe deste ID) e retorna

```python
    async def delete(self, usuario_id: UUID) -> None:
        usuario = await self._repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        await self._repository.delete(usuario)
        await self._invalidate_cache(usuario_id)
```

- Busca o usuário, se não existe lança 404
- Deleta do banco e invalida cache (listagem + detalhe)
- `-> None` = não retorna nada (o router é quem monta a mensagem de resposta)

```python
    async def _invalidate_cache(self, usuario_id: UUID | None = None) -> None:
```

- `_invalidate_cache` = método "privado" (convenção `_`)
- `UUID | None = None` = parâmetro opcional com padrão `None`

```python
        async for key in self._cache.scan_iter(f"{CACHE_KEY_ALL}:*"):
            await self._cache.delete(key)
```

- `async for` = iteração assíncrona — o Redis entrega chaves em lotes
  - `for` normal é síncrono
  - `async for` permite que cada iteração faça `await` internamente

```python
        if usuario_id:
            await self._cache.delete(CACHE_KEY_DETAIL.format(id=usuario_id))
```

- `.format(id=usuario_id)` = substitui `{id}` na string pelo valor
  - `"usuarios:detail:{id}".format(id="abc-123")` → `"usuarios:detail:abc-123"`
  - É a versão mais antiga que f-strings — usada aqui porque a string é uma constante definida antes

---

## 12. router.py — Endpoints HTTP

```python
router = APIRouter()
```

- Cria um roteador que agrupa endpoints (como `@RequestMapping` de uma classe em Spring)

```python
@router.get(
    "",
    response_model=UsuarioPaginatedResponse,
    summary="Listar todos os usuários",
    description="Retorna lista paginada de usuários.",
)
```

- `@` = **decorator** — modifica a função que vem logo abaixo
  - `@router.get("")` = registra a função como handler de `GET /` (relativo ao prefix)
  - É como `@GetMapping("")` em Spring
- `response_model=` = define o tipo da resposta no Swagger/OpenAPI
- `summary=` e `description=` = documentação que aparece no Swagger

```python
async def listar_usuarios(
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginação"),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioPaginatedResponse:
```

- `Query(...)` = marca o parâmetro como **query parameter** da URL (`?limit=10&offset=0`)
- `Depends(get_usuario_service)` = **injeção de dependência** do FastAPI
  - FastAPI chama `get_usuario_service()` automaticamente e injeta o resultado
  - Como `@Autowired` em Spring, mas por parâmetro

```python
    return await service.get_all(limit=limit, offset=offset)
```

- Chama o service e retorna — FastAPI serializa automaticamente para JSON

```python
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
```

- `"/{usuario_id}"` = **path parameter** — o valor vem na URL: `/usuarios/abc-123`
  - É como `@GetMapping("/{id}")` em Spring
- `usuario_id: UUID` = FastAPI extrai automaticamente da URL e converte para UUID
  - Se o valor não for um UUID válido, retorna 422 (Validation Error) automaticamente
- `response_model=UsuarioResponse` = define o formato da resposta JSON

```python
@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_usuario(
    data: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.create(data)
```

- `status_code=status.HTTP_201_CREATED` = retorna 201 ao invés do padrão 200
- `data: UsuarioCreate` = FastAPI lê automaticamente o **body JSON** e valida contra este schema
  - Não precisa de `@RequestBody` como em Java — o tipo Pydantic já indica isso

```python
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
```

- `@router.put` = registra como `PUT /usuarios/{usuario_id}` (como `@PutMapping` em Spring)
- `usuario_id: UUID` = vem da URL (path parameter)
- `data: UsuarioUpdate` = vem do body JSON — como todos os campos são `| None`, aceita partial update
- A função recebe **dois** dados de fontes diferentes: URL (id) e body (dados), FastAPI separa automaticamente

```python
@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_200_OK,
)
async def remover_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> dict:
    await service.delete(usuario_id)
    return {"detail": "Usuário removido com sucesso"}
```

- `"/{usuario_id}"` = path parameter (como `@DeleteMapping("/{id}")` em Spring)
- `-> dict` = retorna um dicionário que vira JSON: `{"detail": "..."}`

---

## 13. dependencies.py (usuarios) — Composição

```python
async def get_usuario_service(
    session: AsyncSession = Depends(get_session),
    cache: redis.Redis = Depends(get_redis),
) -> UsuarioService:
    repository = UsuarioRepository(session)
    return UsuarioService(repository, cache)
```

- Esta função **compõe** as dependências: cria Repository com a session, cria Service com o repository + cache
- O FastAPI resolve a **árvore** Depends:
  1. Chama `get_session()` → obtém session
  2. Chama `get_redis()` → obtém client redis
  3. Chama `get_usuario_service(session, cache)` → obtém o service
  4. Injeta o service no endpoint

---

## 14. main.py — Ponto de Entrada

```python
from contextlib import asynccontextmanager
```

- `asynccontextmanager` = decorator que transforma uma função `yield` em context manager

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
```

- `FastAPI` = classe principal do framework — cria a aplicação
- `CORSMiddleware` = middleware que controla quais origens podem acessar a API
- `get_redoc_html` = função que gera a página HTML do ReDoc (documentação alternativa ao Swagger)

```python
from src.core.config import settings
from src.core.database import engine
from src.core.redis import redis_client
from src.usuarios.models import Base
from src.usuarios.router import router as usuarios_router
```

- Importa objetos dos nossos próprios módulos:
  - `settings` = configurações (env vars)
  - `engine` = motor de conexão com PostgreSQL
  - `redis_client` = cliente Redis
  - `Base` = classe base dos models (contém `.metadata.create_all`)
- `import router as usuarios_router` = renomeia para evitar conflito de nomes

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```

- `@asynccontextmanager` = decorator que transforma esta função no gerenciador de ciclo de vida
- `lifespan` = hook de startup/shutdown do FastAPI

```python
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- `async with` = gerenciador de contexto assíncrono (abre e fecha automaticamente)
- `engine.begin()` = abre uma transação
- `conn.run_sync(funcao)` = executa uma função **síncrona** dentro do contexto assíncrono
  - `Base.metadata.create_all` é síncrona, então precisa deste wrapper

```python
    yield
```

- O `yield` aqui separa **startup** (antes) de **shutdown** (depois)
- Tudo antes do `yield` roda ao iniciar; tudo depois roda ao desligar

```python
    await redis_client.close()
    await engine.dispose()
```

- Fecha conexões limpamente no shutdown

```python
app_configs: dict = {
    "title": "Desafio Jabuti - API de Usuários",
    "description": "API CRUD de usuários com FastAPI, PostgreSQL e Redis",
    "version": "1.0.0",
    "lifespan": lifespan,
    "redoc_url": None,
}
```

- `: dict` = anotação de tipo (é um dicionário)
- Monta as configs como dicionário para passar todas de uma vez
- `"lifespan": lifespan` = passa a função de ciclo de vida que criamos acima
- `"redoc_url": None` = desabilita o ReDoc padrão (vamos criar um customizado depois)

```python
if settings.ENVIRONMENT == "production":
    app_configs["openapi_url"] = None
```

- `dicionario["chave"] = valor` = acessa/modifica por chave (como `.put()` em Java Map)
- Desabilita Swagger em produção

```python
app = FastAPI(**app_configs)
```

- `**app_configs` = **unpacking de dicionário** — espalha como keyword arguments
  - `FastAPI(**{"title": "X", "version": "1.0"})` vira `FastAPI(title="X", version="1.0")`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
```

- Adiciona middleware passando a **classe** (não instância) como primeiro argumento
- O FastAPI instancia internamente
- `allow_origins=` = lista de URLs que podem acessar a API (proteção CORS)
- `allow_credentials=False` = não permite envio de cookies cross-origin
- `allow_methods=` = métodos HTTP permitidos (GET, POST, PUT, DELETE)
- `allow_headers=` = cabeçalhos HTTP aceitos

```python
app.include_router(usuarios_router, prefix="/usuarios", tags=["Usuários"])
```

- Registra o router com prefixo — todos os endpoints ficam sob `/usuarios`
- `tags=["Usuários"]` = agrupamento no Swagger

```python
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
```

- Endpoint direto no `app` (sem router separado)
- Retorna dicionário → FastAPI converte para JSON automaticamente

```python
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )
```

- `@app.get("/redoc", include_in_schema=False)` = cria endpoint GET `/redoc` que **não aparece** no Swagger
  - `include_in_schema=False` = oculta este endpoint da documentação OpenAPI
- `get_redoc_html(...)` = gera a página HTML do ReDoc (documentação alternativa)
- `app.openapi_url` = acessa o atributo da instância `app` (URL do JSON OpenAPI)
- `app.title + " - ReDoc"` = concatenação de strings com `+` (como Java)
- `redoc_js_url=` = fixa a versão 2.1.5 do ReDoc para evitar bugs de versões mais novas

---

## Resumo: Sintaxe Python vs Java

| Conceito | Java | Python |
|---------|------|--------|
| Bloco de código | `{ }` | Indentação (4 espaços) |
| Fim de instrução | `;` | Nova linha |
| Referência a si | `this` | `self` (explícito como parâmetro) |
| Construtor | `public Classe()` | `def __init__(self)` |
| toString | `toString()` | `__repr__()` |
| Herança | `extends` | `class Filha(Pai):` |
| Interface | `implements` | Herança múltipla |
| Null | `null` | `None` |
| Boolean | `true` / `false` | `True` / `False` |
| E lógico | `&&` | `and` |
| OU lógico | `\|\|` | `or` |
| Negação | `!` | `not` |
| Tipo nullable | `Optional<String>` | `str \| None` |
| Generics | `<T>` | `Generic[T]` + `TypeVar` |
| Lambda/Stream | `.stream().map(x -> ...)` | `[f(x) for x in lista]` |
| Interpolação | `String.format()` | `f"texto {variavel}"` |
| Spread/Unpack | Não tem | `**dicionario` ou `*lista` |
| Try/Catch | `try { } catch { }` | `try: ... except: ...` |
| Throw | `throw new Exc()` | `raise Exc()` |
| Async | `CompletableFuture` | `async/await` |
| Privado | `private` keyword | `_` prefixo (convenção) |
| Constante | `static final` | `MAIUSCULO` (convenção) |
| Import | `import com.pkg.Classe` | `from pacote import Classe` |
| Nada/placeholder | `{ }` (corpo vazio) | `pass` |
| Comentário | `//` ou `/* */` | `#` |
| Documentação | `/** Javadoc */` | `"""docstring"""` |
