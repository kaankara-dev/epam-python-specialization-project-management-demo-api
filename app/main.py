from fastapi import FastAPI
from app.db.database import initialize_database
from app.api.v1.endpoints.project import router as project_router

# Canlı sunucu başladığında PostgreSQL veritabanı havuzunu başlatıyoruz:
initialize_database()

app = FastAPI(
    title="Cloud-Native Project & Document Management API",
    version="1.0.0",
)

# Proje endpoint'lerini ana uygulamaya bağlıyoruz:
app.include_router(project_router, prefix="/api/v1")


@app.get("/health")
def get_health():
    return {"status": "ok"}