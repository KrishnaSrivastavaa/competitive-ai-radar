from fastapi import FastAPI

from app.api.competitors import router as competitors_router
from app.api.sources import router as sources_router
from app.core.config import settings
from app.core.database import Base, engine, ensure_sqlite_source_columns

Base.metadata.create_all(bind=engine)
ensure_sqlite_source_columns()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(competitors_router)
app.include_router(sources_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
