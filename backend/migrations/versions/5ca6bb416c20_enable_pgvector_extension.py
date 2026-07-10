"""enable pgvector extension

Revision ID: 5ca6bb416c20
Revises: 
Create Date: 2026-07-07 17:07:44.443625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca6bb416c20'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable the PostgreSQL pgvector extension.

    Creates the `vector` extension when it is not already present so later
    migrations and application features can store vector embeddings.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """
    Disable the PostgreSQL pgvector extension.

    Drops the `vector` extension if it exists. This reverses the migration for
    environments where no remaining database objects depend on pgvector.
    """
    op.execute("DROP EXTENSION IF EXISTS vector")
