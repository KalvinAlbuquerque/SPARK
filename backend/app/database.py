import os
import asyncpg
from pgvector.asyncpg import register_vector
from fastapi import Request

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://spark:changeme@localhost:5432/spark")


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(DATABASE_URL, init=register_vector, min_size=2, max_size=10)


async def get_db(request: Request) -> asyncpg.Pool:
    return request.app.state.pool
