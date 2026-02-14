"""Add LLM configuration to category

Revision ID: 234e4d0def1f
Revises: 123d3c9cdf0e
Create Date: 2026-02-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '234e4d0def1f'
down_revision: Union[str, Sequence[str], None] = '123d3c9cdf0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add LLM configuration columns to categories table
    op.add_column('categories', sa.Column('llm_provider', sa.String(length=50), nullable=False, server_default='openai'))
    op.add_column('categories', sa.Column('llm_model', sa.String(length=100), nullable=False, server_default='gpt-4'))
    op.add_column('categories', sa.Column('llm_provider_type', sa.String(length=50), nullable=False, server_default='direct'))
    op.add_column('categories', sa.Column('llm_api_key', sa.String(length=500), nullable=True))
    op.add_column('categories', sa.Column('llm_endpoint', sa.String(length=500), nullable=True))
    op.add_column('categories', sa.Column('llm_api_version', sa.String(length=50), nullable=True))
    op.add_column('categories', sa.Column('llm_deployment_name', sa.String(length=100), nullable=True))
    op.add_column('categories', sa.Column('llm_region', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove LLM configuration columns from categories table
    op.drop_column('categories', 'llm_region')
    op.drop_column('categories', 'llm_deployment_name')
    op.drop_column('categories', 'llm_api_version')
    op.drop_column('categories', 'llm_endpoint')
    op.drop_column('categories', 'llm_api_key')
    op.drop_column('categories', 'llm_provider_type')
    op.drop_column('categories', 'llm_model')
    op.drop_column('categories', 'llm_provider')

