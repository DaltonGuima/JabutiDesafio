# Desafio Jabuti — API de Usuários

API CRUD de usuários construída com **FastAPI**, **PostgreSQL** e **Redis**, executada via **Docker Compose**.

## Arquitetura

```
src/
├── config.py              # Configurações globais (env vars)
├── database.py            # Conexão assíncrona com PostgreSQL (SQLAlchemy)
├── redis.py               # Conexão com Redis
├── main.py                # Entrypoint da aplicação FastAPI
└── usuarios/
    ├── models.py          # Modelo SQLAlchemy (tabela usuario)
    ├── schemas.py         # Schemas Pydantic (request/response)
    ├── repository.py      # Camada de acesso a dados (Repository Pattern)
    ├── service.py         # Regras de negócio + cache Redis
    ├── router.py          # Endpoints da API
    └── exceptions.py      # Exceções de domínio
```

### Princípios aplicados

- **SOLID**: Cada camada tem responsabilidade única (Single Responsibility). Service depende de abstrações do Repository (Dependency Inversion via FastAPI Depends).
- **Repository Pattern**: Isola operações de banco de dados.
- **Service Layer**: Orquestra regras de negócio e cache, sem conhecer detalhes de HTTP.
- **Clean Architecture**: Router → Service → Repository → Database.

## Endpoints

| Método   | Rota               | Descrição                        |
|----------|--------------------|---------------------------------|
| `GET`    | `/usuarios`        | Lista paginada de usuários       |
| `GET`    | `/usuarios/{id}`   | Detalhe de um usuário            |
| `POST`   | `/usuarios`        | Cria um novo usuário             |
| `PUT`    | `/usuarios/{id}`   | Atualiza um usuário              |
| `DELETE` | `/usuarios/{id}`   | Remove um usuário                |
| `GET`    | `/health`          | Health check                     |

### Paginação

```
GET /usuarios?limit=10&offset=0
```

## Como executar

### Pré-requisitos

- Docker e Docker Compose instalados

### Subir os containers

```bash
docker compose up --build
```

Isso irá iniciar 3 containers:

- **app** — FastAPI na porta `8000`
- **db** — PostgreSQL na porta `5432`
- **cache** — Redis na porta `6379`

### Acessar a documentação

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Cache (Redis)

- Os endpoints `GET /usuarios` e `GET /usuarios/{id}` utilizam Redis como cache.
- TTL padrão: 5 minutos.
- O cache é **invalidado automaticamente** quando um usuário é criado, atualizado ou excluído.

## Variáveis de ambiente

| Variável          | Descrição                     | Padrão                                                  |
|-------------------|-------------------------------|---------------------------------------------------------|
| `DATABASE_URL`    | Connection string PostgreSQL  | `postgresql+asyncpg://jabuti:jabuti_secret@db:5432/jabuti_db` |
| `REDIS_URL`       | Connection string Redis       | `redis://cache:6379/0`                                   |
| `ENVIRONMENT`     | Ambiente (development/production) | `development`                                         |
| `REDIS_CACHE_TTL` | TTL do cache em segundos      | `300`                                                    |
