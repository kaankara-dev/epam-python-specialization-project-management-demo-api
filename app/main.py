from fastapi import FastAPI
from app.db.database import initialize_database
from app.api.v1.endpoints.project import router as project_router
from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.auth import router as auth_router

# Canlı sunucu başladığında PostgreSQL veritabanı havuzunu başlatıyoruz:
initialize_database()

app = FastAPI(
    title="Cloud-Native Project & Document Management API",
    version="1.0.0",
)


app.include_router(project_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
def get_health():
    return {"status": "ok"}