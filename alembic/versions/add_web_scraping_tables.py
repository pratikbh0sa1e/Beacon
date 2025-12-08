"""add web scraping tables

Revision ID: add_web_scraping
Revises: 
Create Date: 2025-12-08 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_web_scraping'
down_revision = 'add_additional_indexes'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create web_scraping_sources table
    op.create_table(
        'web_scraping_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='government'),
        sa.Column('credibility_score', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('scraping_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scraping_frequency', sa.String(length=20), nullable=False, server_default='daily'),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_documents_per_scrape', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('document_section_selector', sa.String(length=200), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.Column('last_scrape_status', sa.String(length=20), nullable=True),
        sa.Column('last_scrape_message', sa.Text(), nullable=True),
        sa.Column('total_documents_scraped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('institution_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_web_sources_enabled', 'web_scraping_sources', ['scraping_enabled'])
    op.create_index('idx_web_sources_institution', 'web_scraping_sources', ['institution_id'])
    
    # Create web_scraping_logs table
    op.create_table(
        'web_scraping_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('documents_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_downloaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scrape_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['web_scraping_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_web_scrape_logs_source_date', 'web_scraping_logs', ['source_id', 'started_at'])
    op.create_index('idx_web_scrape_logs_status', 'web_scraping_logs', ['status'])
    
    # Create scraped_documents table
    op.create_table(
        'scraped_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('source_page', sa.String(length=500), nullable=True),
        sa.Column('source_domain', sa.String(length=200), nullable=False),
        sa.Column('credibility_score', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['web_scraping_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('idx_scraped_docs_source', 'scraped_documents', ['source_id'])
    op.create_index('idx_scraped_docs_domain', 'scraped_documents', ['source_domain'])
    op.create_index('idx_scraped_docs_hash', 'scraped_documents', ['file_hash'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('scraped_documents')
    op.drop_table('web_scraping_logs')
    op.drop_table('web_scraping_sources')
