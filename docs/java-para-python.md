# Java (Spring Boot) → Python (FastAPI) — Mapeamento de Conceitos

Este guia mapeia conceitos que você já conhece de Java/Spring Boot para os equivalentes em Python/FastAPI usados neste projeto.

---

## Visão Geral: Framework

| Java / Spring Boot | Python / FastAPI | Papel |
|-------------------|-----------------|-------|
| Spring Boot | FastAPI | Framework web |
| Spring MVC | FastAPI (Starlette) | Handling de HTTP |
| Tomcat / Netty | Uvicorn | Servidor ASGI/WSGI |
| Maven / Gradle | pip + requirements.txt | Gerenciador de dependências |
| application.yml | pydantic-settings (`.env`) | Configuração |
| JDK 17+ | Python 3.12 | Runtime |

---

## Controller → Router

### Java (Spring Boot)

```java
@RestController
@RequestMapping("/usuarios")
public class UsuarioController {

    @Autowired
    private UsuarioService service;

    @GetMapping
    public ResponseEntity<Page<UsuarioDTO>> listar(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(service.getAll(page, size));
    }

    @GetMapping("/{id}")
    public ResponseEntity<UsuarioDTO> buscar(@PathVariable UUID id) {
        return ResponseEntity.ok(service.getById(id));
    }

    @PostMapping
    public ResponseEntity<UsuarioDTO> criar(@Valid @RequestBody UsuarioCreateDTO data) {
        UsuarioDTO created = service.create(data);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
```

### Python (FastAPI)

```python
router = APIRouter()

@router.get("", response_model=UsuarioPaginatedResponse)
async def listar_usuarios(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioPaginatedResponse:
    return await service.get_all(limit=limit, offset=offset)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def buscar_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.get_by_id(usuario_id)

@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioResponse:
    return await service.create(data)
```

### Diferenças-chave

| Conceito | Spring Boot | FastAPI |
|---------|------------|---------|
| Decorador de classe | `@RestController` | Não tem — usa `APIRouter()` (não é classe) |
| Prefixo de rota | `@RequestMapping("/usuarios")` | `app.include_router(router, prefix="/usuarios")` no `main.py` |
| Injeção no método | `@Autowired` no campo | `Depends()` no parâmetro da função |
| Validação automática | `@Valid` no parâmetro | Automática pelo tipo Pydantic (sempre ativa) |
| Path variable | `@PathVariable UUID id` | Parâmetro com mesmo nome da rota: `usuario_id: UUID` |
| Query param | `@RequestParam` | `Query()` — ou simplesmente declara no parâmetro |
| Request body | `@RequestBody UsuarioCreateDTO data` | Parâmetro com tipo Pydantic: `data: UsuarioCreate` |
| Resposta | `ResponseEntity<T>` | `response_model=T` no decorador + return direto |

---

## DTO → Pydantic Schema

### Java

```java
// DTO de entrada
public record UsuarioCreateDTO(
    @NotBlank @Size(max = 255) String nome,
    @NotBlank @Email String email,
    @Min(0) @Max(150) int idade
) {}

// DTO de saída
public record UsuarioDTO(
    UUID id,
    String nome,
    String email,
    int idade
) {}
```

### Python (Pydantic)

```python
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    idade: int = Field(..., ge=0, le=150)

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioResponse(UsuarioBase):
    id: UUID
    model_config = {"from_attributes": True}  # ← permite converter de ORM model
```

### Mapeamento de Validações

| Java (Bean Validation) | Python (Pydantic) |
|------------------------|-------------------|
| `@NotBlank` | `Field(..., min_length=1)` |
| `@Size(max = 255)` | `Field(..., max_length=255)` |
| `@Email` | `EmailStr` (tipo especial do Pydantic) |
| `@Min(0) @Max(150)` | `Field(..., ge=0, le=150)` |
| `@NotNull` | Campo sem `Optional` / sem valor default |
| `@Valid` | Automático — Pydantic sempre valida |

### Partial Update (PATCH/PUT)

Em Java, partial updates geralmente exigem lógica manual ou bibliotecas como MapStruct.

Em Pydantic, basta declarar campos como `Optional` e usar `exclude_unset=True`:

```python
class UsuarioUpdate(BaseModel):
    nome: str | None = None        # Pode enviar ou não
    email: EmailStr | None = None
    idade: int | None = None

# No repository:
update_data = data.model_dump(exclude_unset=True)  # Só campos que vieram no body
for field, value in update_data.items():
    setattr(usuario, field, value)
```

---

## Entity → SQLAlchemy Model

### Java (JPA/Hibernate)

```java
@Entity
@Table(name = "usuario")
public class Usuario {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 255)
    private String nome;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(nullable = false)
    private int idade;
}
```

### Python (SQLAlchemy 2.0)

```python
class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    idade: Mapped[int] = mapped_column(nullable=False)
```

### Mapeamento ORM

| JPA/Hibernate | SQLAlchemy 2.0 |
|--------------|----------------|
| `@Entity` | Herdar de `DeclarativeBase` |
| `@Table(name = "usuario")` | `__tablename__ = "usuario"` |
| `@Id` | `primary_key=True` no `mapped_column()` |
| `@GeneratedValue(UUID)` | `default=uuid.uuid4` |
| `@Column(nullable, length, unique)` | Parâmetros em `mapped_column()` |
| `EntityManager` | `AsyncSession` |
| `@Transactional` | Gerenciado pelo `get_session()` (commit/rollback automático) |

---

## Repository Pattern

### Java (Spring Data JPA)

```java
@Repository
public interface UsuarioRepository extends JpaRepository<Usuario, UUID> {
    Optional<Usuario> findByEmail(String email);  // Query derivada automática
}
```

### Python (SQLAlchemy manual)

```python
class UsuarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
```

### Diferença principal

**Spring Data JPA** gera queries automáticas pelo nome do método (`findByEmail`). **SQLAlchemy** exige queries explícitas. A contrapartida é ter **controle total** sobre o SQL gerado.

Note que o Repository usa `flush()` e não `commit()`. O commit é feito pelo `get_session()` (dependency) — isso dá controle transacional na camada acima.

| Spring Data JPA | SQLAlchemy |
|----------------|------------|
| `save(entity)` | `session.add(obj)` + `session.flush()` |
| `findById(id)` | `session.get(Model, id)` |
| `deleteById(id)` | `session.delete(obj)` + `session.flush()` |
| `findAll(Pageable)` | `select(Model).limit(n).offset(n)` |
| `@Query("SELECT ...")` | `select(Model).where(...)` |
| `@Transactional` | Gerenciado pelo dependency (yield session + commit/rollback) |

---

## Injeção de Dependência

### Java (Spring)

```java
@Service
public class UsuarioService {

    @Autowired       // ou via construtor
    private UsuarioRepository repository;

    @Autowired
    private RedisTemplate<String, String> cache;
}
```

O Spring escaneia `@Component`, `@Service`, `@Repository` e injeta automaticamente.

### Python (FastAPI Depends)

```python
# Não há container IoC global — a composição é explícita

async def get_usuario_service(
    session: AsyncSession = Depends(get_session),
    cache: redis.Redis = Depends(get_redis),
) -> UsuarioService:
    repository = UsuarioRepository(session)
    return UsuarioService(repository, cache)
```

| Spring | FastAPI |
|--------|---------|
| `@Autowired` | `Depends()` no parâmetro |
| `@Component/@Service/@Repository` | Não existe — composição explícita em funções |
| Container IoC (singleton) | Resolvido por requisição (cada request = novas instâncias) |
| XML / anotações | Funções Python |

### Ciclo de vida das dependências

- **Spring**: Singleton por padrão. Uma instância do Service para toda a aplicação.
- **FastAPI**: Por requisição. Cada request cria uma nova session, um novo repository, um novo service. Exceto dependências "globais" como o `redis_client` que é um singleton.

---

## Exceções e Error Handling

### Java

```java
// Exceção customizada
@ResponseStatus(HttpStatus.NOT_FOUND)
public class UsuarioNaoEncontradoException extends RuntimeException {
    public UsuarioNaoEncontradoException() {
        super("Usuário não encontrado");
    }
}

// Ou com @ControllerAdvice
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UsuarioNaoEncontradoException.class)
    public ResponseEntity<ErrorDTO> handle(UsuarioNaoEncontradoException ex) {
        return ResponseEntity.status(404).body(new ErrorDTO(ex.getMessage()));
    }
}
```

### Python (FastAPI)

```python
class UsuarioNaoEncontrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

# Uso no service:
raise UsuarioNaoEncontrado()  # FastAPI captura e retorna JSON automático
```

| Java | Python/FastAPI |
|------|---------------|
| `RuntimeException` | `Exception` (tudo é unchecked) |
| `@ResponseStatus` | `status_code` no construtor do `HTTPException` |
| `@ControllerAdvice` + `@ExceptionHandler` | Não necessário — `HTTPException` já é tratada pelo FastAPI |
| Checked vs Unchecked | Python não tem checked exceptions |
| `try/catch` | `try/except` |

**Python não tem checked exceptions**. Não precisa declarar `throws` na assinatura dos métodos. As exceções `HTTPException` do FastAPI são automaticamente interceptadas e convertidas em respostas JSON.

---

## Async/Await — Concorrência

### Java

```java
// Java usa threads (Spring MVC padrão) ou reativo (WebFlux)
@GetMapping
public Mono<List<UsuarioDTO>> listar() {    // WebFlux (reativo)
    return service.getAll();
}
```

### Python

```python
@router.get("")
async def listar_usuarios(...) -> UsuarioPaginatedResponse:
    return await service.get_all(limit=limit, offset=offset)
```

| Java | Python |
|------|--------|
| Thread pool (Spring MVC) | Event loop (asyncio) |
| Spring WebFlux / Reactive | `async/await` nativo |
| `CompletableFuture<T>` | `Coroutine[T]` (ou simplesmente `async def`) |
| `Mono<T>`, `Flux<T>` | `await` + tipos normais |

Python usa um **event loop** único (como Node.js). Enquanto uma operação de I/O (query ao banco, request ao Redis) está esperando, o event loop atende outra requisição. Não cria threads — é cooperativo.

---

## Cache com Redis

### Java (Spring Cache)

```java
@Service
public class UsuarioService {

    @Cacheable(value = "usuarios", key = "#id")
    public UsuarioDTO getById(UUID id) {
        return repository.findById(id).map(this::toDTO).orElseThrow();
    }

    @CacheEvict(value = "usuarios", allEntries = true)
    public UsuarioDTO create(UsuarioCreateDTO data) {
        // ...
    }
}
```

Spring Cache usa **anotações declarativas** — o framework cuida de tudo.

### Python (Redis manual)

```python
class UsuarioService:
    async def get_by_id(self, usuario_id: UUID) -> UsuarioResponse:
        cache_key = f"usuarios:detail:{usuario_id}"
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
        # ...
        await self._invalidate_cache()  # Manual
        return response
```

| Spring Cache | FastAPI + Redis |
|-------------|----------------|
| `@Cacheable` | Manual: `cache.get()` → miss → `cache.set()` |
| `@CacheEvict` | Manual: `cache.delete()` / `scan_iter` |
| `@CachePut` | Manual: `cache.set()` |
| `RedisTemplate` | `redis.asyncio.Redis` |
| Serialização automática | `model_dump_json()` / `model_validate_json()` |
| Declarativo | Imperativo (mais verboso, mas mais controle) |

O FastAPI não tem equivalente ao `@Cacheable` do Spring. O cache é implementado **manualmente** no Service, o que dá mais controle mas exige mais código.

---

## Configuração

### Java (application.yml)

```yaml
spring:
  datasource:
    url: jdbc:postgresql://db:5432/jabuti_db
    username: jabuti
    password: jabuti_secret
  redis:
    host: cache
    port: 6379
```

### Python (pydantic-settings)

```python
class Settings(BaseSettings):
    DATABASE_URL: str           # Lê de env var automaticamente
    REDIS_URL: str
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    class Config:
        env_file = ".env"       # Fallback para arquivo local
```

| Spring Boot | FastAPI |
|------------|---------|
| `application.yml` / `application.properties` | Variáveis de ambiente + `.env` |
| `@Value("${property}")` | Campo na classe `Settings` |
| `@ConfigurationProperties` | `BaseSettings` do Pydantic |
| Profiles (`dev`, `prod`) | `ENVIRONMENT` enum |

---

## Resumo de Equivalências Rápidas

| Conceito | Java / Spring Boot | Python / FastAPI |
|---------|-------------------|-----------------|
| Framework | Spring Boot | FastAPI |
| Servidor | Tomcat/Netty | Uvicorn |
| ORM | JPA/Hibernate | SQLAlchemy |
| Validação | Bean Validation (`@Valid`) | Pydantic (automática) |
| DTO | Record/Class | Pydantic `BaseModel` |
| DI | `@Autowired` / construtor | `Depends()` |
| Controller | `@RestController` | `APIRouter()` |
| Repository | `JpaRepository<T, ID>` | Classe Python com `AsyncSession` |
| Service | `@Service` | Classe Python |
| Exceções HTTP | `@ResponseStatus` + `@ControllerAdvice` | `HTTPException` subclass |
| Cache | `@Cacheable/@CacheEvict` | Redis manual no Service |
| Config | `application.yml` | `pydantic-settings` |
| Build | Maven/Gradle | pip + requirements.txt |
| Container | Docker (igual) | Docker (igual) |
| Testes | JUnit + Mockito | pytest + httpx |
| Tipos | Estático (compilação) | Type hints (opcional, checado por mypy) |
| Null safety | `Optional<T>` | `T \| None` |
| Async | WebFlux / `CompletableFuture` | `async/await` nativo |
