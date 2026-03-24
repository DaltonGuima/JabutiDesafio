from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html

from src.core.config import settings
from src.core.database import engine
from src.core.redis import redis_client
from src.usuarios.models import Base
from src.usuarios.router import router as usuarios_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: cria tabelas se não existirem
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: fecha conexões
    await redis_client.close()
    await engine.dispose()


app_configs: dict = {
    "title": "Desafio Jabuti - API de Usuários",
    "description": "API CRUD de usuários com FastAPI, PostgreSQL e Redis",
    "version": "1.0.0",
    "lifespan": lifespan,
    "redoc_url": None,
}

if settings.ENVIRONMENT == "production":
    app_configs["openapi_url"] = None

app = FastAPI(**app_configs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(usuarios_router, prefix="/usuarios", tags=["Usuários"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )
