from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.database import create_pool
from app.routers import internal, pesquisadores, producoes, search, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(
    title="SPARK API",
    description="Plataforma de busca de produções científicas da UNEB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(producoes.router)
app.include_router(pesquisadores.router)
app.include_router(stats.router)
app.include_router(internal.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
