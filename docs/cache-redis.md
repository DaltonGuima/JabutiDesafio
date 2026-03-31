# Cache Redis — Guia Completo

## O que é Cache?

Cache é uma **cópia temporária** de dados em um armazenamento rápido para evitar recalcular ou buscar o dado original repetidamente. Pense assim:

- **Sem cache**: Toda requisição `GET /usuarios` vai ao PostgreSQL → lê do disco → retorna
- **Com cache**: Primeira requisição vai ao PostgreSQL. Resultado é guardado no Redis (memória RAM). Próximas requisições leem do Redis → **muito mais rápido**

### Por que Redis?

| Característica | PostgreSQL | Redis |
|---------------|-----------|-------|
| Armazenamento | Disco (HDD/SSD) | Memória RAM |
| Velocidade típica | ~1-10ms por query | ~0.1-0.5ms por operação |
| Estrutura | Tabelas relacionais | Chave-valor (key-value) |
| Persistência | Total (dados sobrevivem restart) | Opcional (por padrão, dados se perdem no restart) |
| Uso principal | Dados definitivos | Cache, sessões, filas |

Redis é um banco **in-memory** (tudo fica na RAM). Isso o torna ordens de magnitude mais rápido que um banco relacional para leituras simples.

---

## Padrão Cache-Aside (Lazy Loading)

O padrão implementado neste projeto é o **Cache-Aside** (também chamado Lazy Loading):

```
Cliente faz GET /usuarios
         │
         ▼
    ┌─────────┐
    │ Service  │
    └─────────┘
         │
    1. Busca no Redis ──────► Redis tem? ──── SIM ──► Retorna do cache (CACHE HIT)
         │                                               (não toca no banco)
         │ NÃO (CACHE MISS)
         ▼
    2. Busca no PostgreSQL
         │
         ▼
    3. Salva resultado no Redis (com TTL)
         │
         ▼
    4. Retorna para o cliente
```

### Cache Hit vs Cache Miss

- **Cache Hit**: O dado já está no Redis → resposta instantânea, banco nem é consultado
- **Cache Miss**: O dado não está no Redis → consulta o banco → guarda no Redis → responde

---

## Como Funciona no Código

### 1. Chaves de Cache (Cache Keys)

Cada dado cacheado precisa de uma **chave única** para ser encontrado depois:

```python
# service.py
CACHE_KEY_ALL = "usuarios:all"               # Prefixo para listagens
CACHE_KEY_DETAIL = "usuarios:detail:{id}"     # Template para detalhe

# Exemplos de chaves reais no Redis:
# "usuarios:all:limit=10:offset=0"           → listagem página 1
# "usuarios:all:limit=10:offset=10"          → listagem página 2
# "usuarios:detail:550e8400-e29b-41d4-a716-446655440000"  → detalhe de um usuário
```

A convenção de nomes usa `:` como separador — é o padrão do Redis, semelhante a namespaces.

### 2. Leitura com Cache (GET)

```python
async def get_all(self, *, limit: int, offset: int) -> UsuarioPaginatedResponse:
    # 1. Monta a chave baseada nos parâmetros da paginação
    cache_key = f"{CACHE_KEY_ALL}:limit={limit}:offset={offset}"

    # 2. Tenta buscar no Redis
    cached = await self._cache.get(cache_key)
    if cached:
        # CACHE HIT: deserializa o JSON do Redis e retorna
        return UsuarioPaginatedResponse.model_validate_json(cached)

    # 3. CACHE MISS: busca no banco de dados
    usuarios = await self._repository.get_all(limit=limit, offset=offset)
    total = await self._repository.count()

    # 4. Monta o response
    response = UsuarioPaginatedResponse(
        items=[UsuarioResponse.model_validate(u) for u in usuarios],
        total=total,
        limit=limit,
        offset=offset,
    )

    # 5. Salva no Redis com TTL (expira automaticamente depois de X segundos)
    await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)

    return response
```

Passo a passo:

1. A chave é construída com os parâmetros da requisição (`limit=10:offset=0`)
2. `self._cache.get(cache_key)` busca o valor no Redis → retorna `None` se não existir
3. Se encontrou (string JSON), `model_validate_json()` converte de volta para objeto Pydantic
4. Se não encontrou, faz a query normal no PostgreSQL
5. `self._cache.set(key, value, ex=300)` salva o JSON no Redis por 300 segundos (5 min)

### 3. Detalhe com Cache (GET by ID)

```python
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
```

Mesma lógica, mas a chave inclui o UUID do usuário: `usuarios:detail:550e8400-...`

---

## Invalidação de Cache

> *"There are only two hard things in Computer Science: cache invalidation and naming things."* — Phil Karlton

### O Problema

Quando um dado muda (CREATE, UPDATE, DELETE), o cache fica **desatualizado** (stale). Se alguém faz `GET /usuarios` e o cache retorna dados antigos, o usuário vê informação incorreta.

### A Solução: Invalidar no CUD

Toda operação que **modifica dados** (Create, Update, Delete) invalida o cache:

```python
async def create(self, data: UsuarioCreate) -> UsuarioResponse:
    # ... cria no banco ...
    await self._invalidate_cache()          # ← invalida TODAS as listagens
    return UsuarioResponse.model_validate(usuario)

async def update(self, usuario_id: UUID, data: UsuarioUpdate) -> UsuarioResponse:
    # ... atualiza no banco ...
    await self._invalidate_cache(usuario_id)  # ← invalida listagens + detalhe deste ID
    return UsuarioResponse.model_validate(updated)

async def delete(self, usuario_id: UUID) -> None:
    # ... deleta do banco ...
    await self._invalidate_cache(usuario_id)  # ← invalida listagens + detalhe deste ID
```

### Método de Invalidação

```python
async def _invalidate_cache(self, usuario_id: UUID | None = None) -> None:
    # 1. Remove TODAS as chaves de listagem paginada
    async for key in self._cache.scan_iter(f"{CACHE_KEY_ALL}:*"):
        await self._cache.delete(key)

    # 2. Remove cache do detalhe específico (se informado)
    if usuario_id:
        await self._cache.delete(CACHE_KEY_DETAIL.format(id=usuario_id))
```

#### O que é `scan_iter`?

O Redis armazena milhões de chaves. O comando `SCAN` percorre as chaves de forma **incremental** , sem bloquear o servidor (diferente do perigoso comando `KEYS`).

`scan_iter("usuarios:all:*")` encontra todas as chaves que começam com `usuarios:all:`:

- `usuarios:all:limit=10:offset=0`
- `usuarios:all:limit=10:offset=10`
- `usuarios:all:limit=20:offset=0`
- etc.

Todas são deletadas, pois quando a lista muda, TODAS as páginas podem estar desatualizadas.

#### Por que invalidar ao invés de atualizar?

| Estratégia | Prós | Contras |
|-----------|------|--------|
| **Invalidar** (nosso caso) | Simples, sempre consistente | Próximo GET terá cache miss |
| **Atualizar** (write-through) | Sem cache miss | Complexo, pode causar inconsistências em sistemas distribuídos |

Para uma API CRUD simples, **invalidar é a escolha correta**. O custo de um cache miss ocasional é insignificante.

---

## TTL (Time To Live)

```python
# config.py
REDIS_CACHE_TTL: int = 300  # 5 minutos

# service.py — ao salvar no cache
await self._cache.set(cache_key, response.model_dump_json(), ex=self._ttl)
#                                                             ^^^^^^^^^^
#                                         ex = expire in seconds (300s = 5min)
```

O TTL é uma **rede de segurança**: mesmo que a invalidação falhe por algum motivo, o dado expira sozinho em 5 minutos. Isso garante que dados **muito** antigos nunca sejam servidos.

### Como o TTL funciona internamente

1. Redis armazena o par `chave → valor` com um **timestamp de expiração**
2. Um processo interno do Redis (lazy expiration + active expiration) remove chaves expiradas
3. Se alguém faz `GET` de uma chave expirada, Redis retorna `None` — como se a chave não existisse

---

## Serialização: JSON no Redis

O Redis armazena **strings**. Nossos dados são objetos Python. Precisamos converter:

```python
# Serializar (objeto Python → JSON string para o Redis)
response.model_dump_json()
# Resultado: '{"items":[{"id":"550e...","nome":"João","email":"joao@email.com","idade":25}],...}'

# Deserializar (JSON string do Redis → objeto Python)
UsuarioPaginatedResponse.model_validate_json(cached)
# Resultado: UsuarioPaginatedResponse(items=[UsuarioResponse(id=UUID('550e...'), ...)])
```

O Pydantic faz isso nativamente com `model_dump_json()` e `model_validate_json()` — sem precisar de `json.dumps/loads` manual.

---

## Configuração do Cliente Redis

```python
# core/redis.py
import redis.asyncio as redis

redis_client = redis.from_url(
    settings.REDIS_URL,          # "redis://cache:6379/0"
    decode_responses=True,        # ← retorna strings ao invés de bytes
)
```

### A URL `redis://cache:6379/0`

| Parte | Significado |
|-------|-------------|
| `redis://` | Protocolo Redis |
| `cache` | Hostname do container Redis (nome do service no docker-compose) |
| `6379` | Porta padrão do Redis |
| `/0` | Database number (Redis tem 16 databases: 0-15) |

### `decode_responses=True`

Por padrão, o Redis retorna dados como `bytes` (`b'{"nome":"João"}'`). Com `decode_responses=True`, converte automaticamente para `str` — evitando `.decode('utf-8')` em todo lugar.

---

## Fluxo Visual Completo

### GET /usuarios (primeira vez — CACHE MISS)

```
Cliente ──GET──► Router ──► Service ──► Redis.get("usuarios:all:limit=10:offset=0")
                                              │
                                         retorna None (miss)
                                              │
                                    Service ──► Repository ──► PostgreSQL
                                              │                    │
                                         ◄────┘  [Usuario, ...]   │
                                              │                    │
                                    Service ──► Redis.set(key, JSON, ex=300)
                                              │
                              ◄───────────────┘  UsuarioPaginatedResponse
```

### GET /usuarios (segunda vez — CACHE HIT)

```
Cliente ──GET──► Router ──► Service ──► Redis.get("usuarios:all:limit=10:offset=0")
                                              │
                                         retorna JSON (hit!)
                                              │
                                    Service deserializa JSON
                                              │
                              ◄───────────────┘  UsuarioPaginatedResponse
                              (PostgreSQL NÃO foi consultado!)
```

### POST /usuarios (cria + invalida)

```
Cliente ──POST──► Router ──► Service ──► Repository.create() ──► PostgreSQL
                                              │
                                    Service ──► Redis.scan_iter("usuarios:all:*")
                                              │     → deleta cada chave encontrada
                                              │
                              ◄───────────────┘  UsuarioResponse (201 Created)
```

---

## Resumo: Decisões de Design

| Decisão | Motivo |
|---------|--------|
| **Cache-Aside** (não write-through) | Simplicidade e consistência |
| **Invalidação no CUD** (não atualização) | Evita inconsistências; custo de miss é baixo |
| **TTL de 5 minutos** | Rede de segurança contra dados stale |
| **scan_iter** (não KEYS) | Não bloqueia o Redis em produção |
| **JSON como formato** | Legível, suportado nativamente pelo Pydantic |
| **decode_responses=True** | Evita manipulação manual de bytes |
| **Cache no Service** (não no Router) | O Router não deve conhecer detalhes de cache |
| **Chaves com parâmetros** | Cada combinação de paginação tem seu próprio cache |
