from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.blob import ensure_bucket
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import ai, applications, auth
from app.seed import seed_demo_officer


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_demo_officer(session)
    ensure_bucket()
    yield


app = FastAPI(
    title="BLLRO Land Mutation and Verification Assistant",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(ai.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
