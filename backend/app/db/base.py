from sqlalchemy.orm import DeclarativeBase


# Base is the parent class for all SQLAlchemy ORM models.
# Every model that inherits from Base becomes part of: Base.metadata
# Alembic needs this metadata to detect tables and columns.
class Base(DeclarativeBase):
    pass