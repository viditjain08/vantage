"""Add resource_config to mcp_servers

Revision ID: 345f5e1ef2g0
Revises: 234e4d0def1f
Create Date: 2026-02-14 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '345f5e1ef2g0'
down_revision: Union[str, Sequence[str], None] = '234e4d0def1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resource_config JSON column to mcp_servers table."""
    op.add_column('mcp_servers', sa.Column('resource_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove resource_config column from mcp_servers table."""
    op.drop_column('mcp_servers', 'resource_config')
