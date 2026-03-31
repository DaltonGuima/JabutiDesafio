# Relatório de Testes — API de Usuários

**Data:** 24/03/2026  
**Ambiente:** Docker Compose (3 containers: app, db, cache)  
**Base URL:** `http://localhost:8000`

---

## Resumo

| Total de Testes | Aprovados | Reprovados |
|:---:|:---:|:---:|
| 15 | 15 | 0 |

---

## 1. Health Check

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 1 | `GET` | `/health` | Verificação de saúde da API | 200 | 200 | PASS |

**Response:**

```json
{"status": "ok"}
```

---

## 2. POST /usuarios — Criação

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 2 | `POST` | `/usuarios` | Criar usuário com dados válidos | 201 | 201 | PASS |
| 3 | `POST` | `/usuarios` | Criar com email já existente | 409 | 409 | PASS |
| 4 | `POST` | `/usuarios` | Body com dados inválidos (nome vazio, email inválido, idade negativa) | 422 | 422 | PASS |

**Teste 2 — Request:**

```json
{"nome": "Maria Souza", "email": "maria@email.com", "idade": 25}
```

**Response (201):**

```json
{
  "nome": "Maria Souza",
  "email": "maria@email.com",
  "idade": 25,
  "id": "c6566c4f-62a5-4613-923d-a67965a2d3da"
}
```

**Teste 3 — Email duplicado (409):**

```json
{"detail": "Email já cadastrado"}
```

**Teste 4 — Validação Pydantic (422):**

```json
{
  "detail": [
    {"type": "string_too_short", "loc": ["body","nome"], "msg": "String should have at least 1 character"},
    {"type": "value_error", "loc": ["body","email"], "msg": "value is not a valid email address: An email address must have an @-sign."},
    {"type": "greater_than_equal", "loc": ["body","idade"], "msg": "Input should be greater than or equal to 0"}
  ]
}
```

---

## 3. GET /usuarios — Listagem com Paginação

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 5 | `GET` | `/usuarios?limit=10&offset=0` | Listar todos (2 usuários) | 200 | 200 | PASS |
| 6 | `GET` | `/usuarios?limit=1&offset=0` | Página 1 (1 item) | 200 | 200 | PASS |
| 7 | `GET` | `/usuarios?limit=1&offset=1` | Página 2 (1 item) | 200 | 200 | PASS |

**Teste 5 — Listagem completa (200):**

```json
{
  "items": [
    {"nome": "Carlos Silva", "email": "carlos@email.com", "idade": 30, "id": "e763f3d6-..."},
    {"nome": "Maria Souza", "email": "maria@email.com", "idade": 25, "id": "c6566c4f-..."}
  ],
  "total": 2,
  "limit": 10,
  "offset": 0
}
```

**Teste 6 — Paginação limit=1, offset=0 (200):**

```json
{
  "items": [{"nome": "Carlos Silva", "email": "carlos@email.com", "idade": 30, "id": "e763f3d6-..."}],
  "total": 2,
  "limit": 1,
  "offset": 0
}
```

**Teste 7 — Paginação limit=1, offset=1 (200):**

```json
{
  "items": [{"nome": "Maria Souza", "email": "maria@email.com", "idade": 25, "id": "c6566c4f-..."}],
  "total": 2,
  "limit": 1,
  "offset": 1
}
```

---

## 4. GET /usuarios/{id} — Detalhe

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 8 | `GET` | `/usuarios/{id}` | Buscar usuário existente | 200 | 200 | PASS |
| 9 | `GET` | `/usuarios/{id}` | Buscar ID inexistente | 404 | 404 | PASS |

**Teste 8 — Detalhe (200):**

```json
{
  "nome": "Carlos Silva",
  "email": "carlos@email.com",
  "idade": 30,
  "id": "e763f3d6-c730-40a9-a188-6cfb4ba2ae9a"
}
```

**Teste 9 — Não encontrado (404):**

```json
{"detail": "Usuário não encontrado"}
```

---

## 5. PUT /usuarios/{id} — Atualização

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 10 | `PUT` | `/usuarios/{id}` | Atualizar nome e idade | 200 | 200 | PASS |
| 11 | `PUT` | `/usuarios/{id}` | Atualizar email para um já existente | 409 | 409 | PASS |
| 12 | `PUT` | `/usuarios/{id}` | Atualizar ID inexistente | 404 | 404 | PASS |

**Teste 10 — Atualização parcial (200):**

```
Request:  {"nome": "Carlos Atualizado", "idade": 31}
Response: {"nome": "Carlos Atualizado", "email": "carlos@email.com", "idade": 31, "id": "e763f3d6-..."}
```

**Teste 11 — Email duplicado no update (409):**

```json
{"detail": "Email já cadastrado"}
```

**Teste 12 — ID inexistente no update (404):**

```json
{"detail": "Usuário não encontrado"}
```

---

## 6. DELETE /usuarios/{id} — Remoção

| # | Método | Endpoint | Descrição | Status Esperado | Status Obtido | Resultado |
|---|--------|----------|-----------|:---:|:---:|:---:|
| 13 | `DELETE` | `/usuarios/{id}` | Remover usuário existente | 204 | 204 | PASS |
| 14 | `DELETE` | `/usuarios/{id}` | Remover mesmo usuário novamente | 404 | 404 | PASS |
| 15 | `DELETE` | `/usuarios/{id}` | Remover ID inexistente | 404 | 404 | PASS |

**Teste 13 — Remoção bem-sucedida:** Status `204 No Content` (sem body)

**Teste 14/15 — Já removido / inexistente (404):**

```json
{"detail": "Usuário não encontrado"}
```

---

## 7. Validação do Cache Redis

| Cenário | Comportamento Esperado | Resultado |
|---------|----------------------|:---:|
| GET /usuarios após primeiro acesso | Resposta armazenada no Redis (TTL 300s) | PASS |
| GET /usuarios/{id} após primeiro acesso | Resposta armazenada no Redis (TTL 300s) | PASS |
| POST /usuarios (criar) | Cache de listagem invalidado | PASS |
| PUT /usuarios/{id} (atualizar) | Cache de listagem + detalhe invalidados | PASS |
| DELETE /usuarios/{id} (remover) | Cache de listagem + detalhe invalidados | PASS |
| GET /usuarios após DELETE | Retorna lista atualizada (1 usuário) | PASS |

---

## 8. Verificação de Infraestrutura Docker

| Container | Imagem | Status | Porta |
|-----------|--------|:---:|:---:|
| `fastapi-app` | python:3.12-slim (custom) | Running | 8000 |
| `fastapi-db` | postgres:16-alpine | Healthy | 5432 |
| `fastapi-cache` | redis:7-alpine | Healthy | 6379 |

- Volume persistente: `postgres_data` (PostgreSQL)
- Rede: `jabuti-network` (bridge)
- Health checks: PostgreSQL (`pg_isready`) e Redis (`redis-cli ping`)

---

## Conclusão

Todos os **15 testes** passaram com sucesso. A API atende integralmente aos requisitos funcionais e técnicos do desafio:

- **CRUD completo** com os 5 endpoints especificados
- **Paginação** funcional com `limit` e `offset`
- **UUID automático** como identificador
- **Email único** com validação e tratamento de conflito (409)
- **Validação de entrada** via Pydantic (422)
- **Cache Redis** nos GETs com invalidação nos CUDs
- **Docker Compose** com 3 containers separados (app, db, cache)
- **PostgreSQL** com volume persistente
- **CORS** configurado para segurança básica
