from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.internal import router as internal_router
from app.api.v1.endpoints.invitation import router as invitation_router
from app.api.v1.endpoints.project import router as project_router
from app.db.database import initialize_database
from app.db.registry import MODELS


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama ayağa kalkarken otomatik çalışır:
    target_database = initialize_database()
    with target_database:
        target_database.create_tables(MODELS, safe=True)

    yield

    # Uygulama kapanırken (varsa bağlantıyı kapatma vb.)
    if not target_database.is_closed():
        target_database.close()


app = FastAPI(
    title="Cloud-Native Project & Document Management API",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(project_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(invitation_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")


@app.get("/health")
def get_health():
    return {"status": "ok"}