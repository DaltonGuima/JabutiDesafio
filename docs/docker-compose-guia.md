# Docker e Docker Compose — Guia Completo

## Conceitos Fundamentais

### O que é Docker?

Docker é uma ferramenta que empacota sua aplicação junto com **tudo que ela precisa** (sistema operacional, bibliotecas, dependências) em uma unidade chamada **container**.

Sem Docker:

```
"Funciona na minha máquina" → instalar Python, pip, PostgreSQL, Redis, configurar tudo manualmente
```

Com Docker:

```
"docker compose up" → tudo roda igual em qualquer máquina
```

### Container vs Imagem

| Conceito | Analogia | Descrição |
|---------|---------|-----------|
| **Imagem** | Classe (Java) | Template imutável — define O QUE vai rodar |
| **Container** | Objeto (instância) | Processo em execução — criado A PARTIR de uma imagem |

Uma **imagem** é um pacote estático (arquivo). Um **container** é essa imagem rodando como processo.

```
Imagem "python:3.12-slim" ─── docker run ───► Container rodando Python
Imagem "postgres:16-alpine" ─── docker run ───► Container rodando PostgreSQL
```

### Container vs Máquina Virtual

| Aspecto | Container | Máquina Virtual |
|---------|----------|-----------------|
| Peso | ~50-200MB | ~2-10GB |
| Startup | Segundos | Minutos |
| Isolamento | Compartilha kernel do host | Kernel próprio |
| Performance | ~nativa | Overhead de virtualização |

Containers são **leves** porque compartilham o kernel do sistema operacional host. Cada container é apenas um processo isolado.

---

## Dockerfile — Receita da Imagem

O `Dockerfile` é uma **receita passo a passo** para construir a imagem da aplicação:

```dockerfile
# 1. Base: começa com Python 3.12 (versão slim = sem pacotes extras)
FROM python:3.12-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Instala dependências do sistema (gcc é necessário para compilar alguns pacotes Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Copia APENAS o requirements.txt primeiro (otimização de cache de build)
COPY requirements.txt .

# 5. Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia o restante do código
COPY . .

# 7. Documenta que a aplicação usa a porta 8000
EXPOSE 8000

# 8. Comando que roda quando o container inicia
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Explicação linha por linha

#### `FROM python:3.12-slim`

A base da imagem. `slim` é uma versão enxuta do Debian com Python pré-instalado (~150MB vs ~900MB da versão full). Outras opções:

- `python:3.12` — versão completa (maior, mais pacotes do sistema)
- `python:3.12-alpine` — baseada em Alpine Linux (~50MB), mas pode ter problemas de compatibilidade

#### `WORKDIR /app`

Cria e define `/app` como diretório de trabalho. Todos os comandos subsequentes rodam neste diretório. É como fazer `cd /app`.

#### `RUN apt-get update && ...`

Executa comandos durante o **build** da imagem. Aqui instala `gcc` (compilador C), necessário para compilar a extensão C do `asyncpg` (driver PostgreSQL).

- `--no-install-recommends` → não instala pacotes recomendados (reduz tamanho)
- `rm -rf /var/lib/apt/lists/*` → limpa cache do apt (reduz tamanho)

#### `COPY requirements.txt .` + `RUN pip install ...`

**Otimização de cache de build**: Copiando APENAS o `requirements.txt` antes do resto do código, o Docker **cacheia** a instalação de dependências. Se você mudar o código (mas não as dependências), o Docker reutiliza a camada do `pip install` — rebuild muito mais rápido.

```
Camada 1: FROM python:3.12-slim           ← cacheada (não muda)
Camada 2: RUN apt-get install gcc          ← cacheada (não muda)
Camada 3: COPY requirements.txt            ← cacheada (se requirements não mudou)
Camada 4: RUN pip install                  ← cacheada (se requirements não mudou)
Camada 5: COPY . .                         ← RECONSTRUÍDA (código mudou)
```

#### `EXPOSE 8000`

Apenas **documentação** — declara que o container escuta na porta 8000. Não abre a porta automaticamente (isso é feito no `docker-compose.yml` com `ports`).

#### `CMD ["uvicorn", "src.main:app", ...]`

Comando padrão quando o container inicia. Usa formato **exec** (array JSON) ao invés de shell — mais seguro, sinais do SO chegam diretamente ao processo.

- `--host 0.0.0.0` → escuta em todas as interfaces (necessário dentro do container)
- `--port 8000` → porta interna do container
- `--reload` → hot-reload em desenvolvimento (reinicia quando código muda)

---

## Docker Compose — Orquestração de Múltiplos Containers

O `docker-compose.yml` define e orquestra **múltiplos containers** que formam a aplicação:

```yaml
services:
  app:                          # Serviço 1: aplicação FastAPI
    build:
      context: .                # Usa o Dockerfile na raiz do projeto
      dockerfile: Dockerfile
    container_name: fastapi-app
    ports:
      - "8000:8000"            # Mapeia porta host:container
    environment:                # Variáveis de ambiente
      - DATABASE_URL=postgresql+asyncpg://jabuti:jabuti_secret@db:5432/jabuti_db
      - REDIS_URL=redis://cache:6379/0
      - ENVIRONMENT=development
    depends_on:                 # Ordem de inicialização
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    volumes:
      - ./src:/app/src          # Mount do código fonte para hot-reload
    networks:
      - jabuti-network

  db:                           # Serviço 2: banco PostgreSQL
    image: postgres:16-alpine   # Usa imagem pronta do Docker Hub
    container_name: fastapi-db
    environment:
      POSTGRES_USER: jabuti
      POSTGRES_PASSWORD: jabuti_secret
      POSTGRES_DB: jabuti_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data   # Volume persistente
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jabuti -d jabuti_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - jabuti-network

  cache:                        # Serviço 3: cache Redis
    image: redis:7-alpine
    container_name: fastapi-cache
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - jabuti-network

volumes:
  postgres_data:                # Declaração do volume nomeado

networks:
  jabuti-network:
    driver: bridge              # Cria rede isolada para os containers
```

---

## Conceitos Detalhados

### Ports (Mapeamento de Portas)

```yaml
ports:
  - "8000:8000"   # HOST:CONTAINER
```

```
Sua máquina                    Container
(localhost)                    (fastapi-app)
                               
Port 8000  ◄─── mapeamento ──► Port 8000
```

- A porta da **esquerda** é a do seu computador (host)
- A porta da **direita** é a interna do container
- Sem esse mapeamento, não há como acessar o container de fora

Poderia ser `"3000:8000"` — acessaria via `localhost:3000`, mas internamente o container continua na 8000.

### Environment (Variáveis de Ambiente)

```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://jabuti:jabuti_secret@db:5432/jabuti_db
```

Variáveis de ambiente são injetadas dentro do container. O `pydantic-settings` as lê automaticamente em `config.py`.

Detalhe importante na URL do banco:

```
postgresql+asyncpg://jabuti:jabuti_secret@db:5432/jabuti_db
                                          ^^
                                      hostname "db"
```

O hostname `db` é o **nome do serviço** no `docker-compose.yml`. O Docker Compose cria um DNS interno onde cada service é acessível pelo nome. Não é `localhost` — é o nome do container na rede Docker.

### depends_on + Healthcheck

```yaml
depends_on:
  db:
    condition: service_healthy  # Espera o banco estar SAUDÁVEL (não só iniciado)
  cache:
    condition: service_healthy
```

Sem `condition: service_healthy`, o Docker Compose inicia os containers na ordem, mas **não espera** o serviço estar pronto. O container do PostgreSQL pode iniciar em 1 segundo, mas levar mais 3 para aceitar conexões.

O **healthcheck** define como verificar se o serviço está pronto:

```yaml
# PostgreSQL: roda pg_isready a cada 5s, até 5 tentativas
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U jabuti -d jabuti_db"]
  interval: 5s      # Verifica a cada 5 segundos
  timeout: 5s       # Se demorar mais de 5s, considera falha
  retries: 5        # Após 5 falhas consecutivas, marca como unhealthy

# Redis: roda redis-cli ping — retorna PONG se está pronto
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
```

Sequência de startup:

```
1. db inicia       ─── healthcheck verifica ──── "pg_isready" retorna OK ✓
2. cache inicia    ─── healthcheck verifica ──── "redis-cli ping" retorna PONG ✓
3. app inicia      ─── (só agora, porque depends_on espera ambos healthy)
```

### Volumes

#### Volume Nomeado (dados persistentes)

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:    # Declaração no nível raiz
```

O Docker cria um **volume gerenciado** chamado `postgres_data`. Os dados do PostgreSQL são armazenados neste volume, que **sobrevive** ao `docker compose down` e `docker compose up` — os dados não se perdem.

```
docker compose down    → container é destruído, mas o volume fica
docker compose up      → novo container, mesmo volume → dados preservados
docker compose down -v → DESTRÓI o volume também (cuidado!)
```

#### Bind Mount (código fonte)

```yaml
services:
  app:
    volumes:
      - ./src:/app/src    # HOST_PATH:CONTAINER_PATH
```

Um **bind mount** espelha uma pasta do seu computador dentro do container:

```
Seu computador          Container
./src/main.py  ◄═══►  /app/src/main.py
```

Quando você edita `src/main.py` no VS Code, a mudança aparece **instantaneamente** dentro do container. Combinado com `--reload` do Uvicorn, o servidor reinicia automaticamente. É o que permite **hot-reload** em desenvolvimento.

**Diferença volume vs bind mount**:

- **Volume nomeado** (`postgres_data:/var/lib/...`): gerenciado pelo Docker, bom para dados que devem persistir
- **Bind mount** (`./src:/app/src`): espelha pasta do host, bom para desenvolvimento

### Networks

```yaml
networks:
  jabuti-network:
    driver: bridge
```

Cria uma **rede isolada** para os containers do projeto. Somente containers na mesma rede podem se comunicar entre si.

```
┌──────────────────── jabuti-network ────────────────────┐
│                                                         │
│  fastapi-app ◄────► fastapi-db ◄────► fastapi-cache    │
│  (app)              (db)              (cache)           │
│                                                         │
└─────────────────────────────────────────────────────────┘

Outros containers (de outros projetos) NÃO acessam esta rede.
```

O **driver bridge** é o padrão — cria uma rede local virtual. Alternativas:

- `host`: container usa a rede do host diretamente (sem isolamento)
- `overlay`: para clusters Docker Swarm (múltiplas máquinas)

### DNS interno do Docker

Dentro da rede `jabuti-network`, cada container é acessível pelo **nome do service**:

```
app → DATABASE_URL=...@db:5432/...     ← "db" resolve para o IP do container PostgreSQL
app → REDIS_URL=redis://cache:6379/0   ← "cache" resolve para o IP do container Redis
```

Não precisamos saber o IP dos containers — o Docker resolve o nome automaticamente.

---

## Comandos Docker Compose Essenciais

```bash
# Subir todos os containers (build se necessário)
docker compose up -d --build
# -d = detached (roda em background)
# --build = reconstrói a imagem da app

# Ver logs de todos os containers
docker compose logs -f
# -f = follow (fica acompanhando em tempo real)

# Ver logs de um container específico
docker compose logs -f app

# Ver containers rodando
docker compose ps

# Parar e remover containers
docker compose down

# Parar, remover containers E volumes (APAGA DADOS DO BANCO!)
docker compose down -v

# Reconstruir apenas a imagem da app
docker compose build app

# Executar comando dentro de um container rodando
docker compose exec app bash          # Abrir shell dentro do container da app
docker compose exec db psql -U jabuti # Abrir console do PostgreSQL
docker compose exec cache redis-cli   # Abrir console do Redis
```

---

## Build vs Image

No `docker-compose.yml`, um service pode usar:

```yaml
# OPÇÃO 1: build — constrói a imagem a partir de um Dockerfile
app:
  build:
    context: .
    dockerfile: Dockerfile

# OPÇÃO 2: image — usa imagem pronta do Docker Hub
db:
  image: postgres:16-alpine
```

- `build`: para **sua aplicação** (código único do projeto)
- `image`: para **serviços de infraestrutura** (banco, cache, message broker, etc.)

---

## Otimizações Aplicadas

### 1. Multi-stage? Não necessário

Para APIs Python simples, um Dockerfile single-stage com `slim` é suficiente. Multi-stage é mais útil quando:

- Há etapa de compilação pesada (ex: frontend React)
- A imagem final pode ser significativamente menor sem ferramentas de build

### 2. Alpine para PostgreSQL e Redis

```yaml
db:
  image: postgres:16-alpine    # ~80MB vs ~400MB da versão Debian
cache:
  image: redis:7-alpine        # ~30MB vs ~130MB da versão Debian
```

Alpine Linux é uma distribuição mínima (~5MB). Para serviços de infraestrutura é ideal — menos superfície de ataque, mas para Python pode gerar problemas com pacotes compilados (por isso a app usa `slim` e não `alpine`).

### 3. `--no-cache-dir` no pip

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Impede o pip de guardar cache de downloads dentro da imagem — reduz tamanho final.

### 4. Limpeza de apt

```dockerfile
RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*
```

Tudo em um único `RUN` e limpa o cache no final — reduz tamanho da camada.

---

## Fluxo Completo: Do `docker compose up` à API Rodando

```
1. docker compose up -d --build

2. Docker lê docker-compose.yml
   ├── Service "db":   Puxa imagem postgres:16-alpine do Docker Hub
   ├── Service "cache": Puxa imagem redis:7-alpine do Docker Hub
   └── Service "app":  Constrói imagem a partir do Dockerfile

3. Docker inicia containers na ordem:
   ├── db inicia     → PostgreSQL começa aceitar conexões (healthcheck OK)
   ├── cache inicia  → Redis responde PONG (healthcheck OK)
   └── app inicia    → (depends_on espera db e cache estarem healthy)

4. Container "app" executa CMD:
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

5. FastAPI executa lifespan (startup):
   └── CREATE TABLE IF NOT EXISTS usuario ...

6. API pronta em http://localhost:8000
   ├── /docs      → Swagger UI
   ├── /redoc     → ReDoc
   └── /usuarios  → CRUD endpoints
```
