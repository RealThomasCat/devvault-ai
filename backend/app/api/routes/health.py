from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


# Health Check Endpoint for Application
@router.get("/health")
def health_check() -> dict[str, str]:
    """
    Return application health and runtime metadata.

    The endpoint performs an in-process health check and exposes the configured
    application name and environment so deployments can verify that the expected
    service instance is responding.

    Returns:
        A status payload containing the service health, name, and environment.
    """
    settings = get_settings()

    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }


# Health Check Endpoint for Database
@router.get("/health/db")
def database_health_check(db: Session = Depends(get_db)) -> dict[str, str | int]: # FastAPI will call get_db(), receive the DB session, and pass it into db.
    """
    Verify that the configured database is reachable.

    Executes a minimal SQL query through the request-scoped database session to
    confirm that the application can acquire a working database connection.

    Args:
        db: SQLAlchemy session provided by FastAPI dependency injection.

    Returns:
        A status payload confirming database reachability and the probe result.

    Raises:
        HTTPException: If the database query fails or the database cannot be
        reached.
    """
    try:
        result = db.execute(text("SELECT 1")).scalar_one()

        return {
            "status": "ok",
            "database": "reachable",
            "result": result,
        }

    # If SQLAlchemy/Postgres connection fails, we return HTTP 503 Service Unavailable.
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable",
        ) from exc
