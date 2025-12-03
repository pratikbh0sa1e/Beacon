"""merge chat and workflow heads

Revision ID: b316767083e4
Revises: add_document_chat, add_document_workflow
Create Date: 2025-12-03 16:35:14.796316

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b316767083e4'
down_revision = ('add_document_chat', 'add_document_workflow')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
