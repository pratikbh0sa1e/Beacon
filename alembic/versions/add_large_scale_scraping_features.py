"""add large scale scraping features

Revision ID: add_large_scale_scraping
Revises: add_web_scraping
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_large_scale_scraping'
down_revision = 'add_web_scraping'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to web_scraping_sources for pagination and scheduling
    op.add_column('web_scraping_sources', sa.Column('pagination_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('web_scraping_sources', sa.Column('max_pages', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('web_scraping_sources', sa.Column('schedule_type', sa.String(length=20), nullable=True))
    op.add_column('web_scraping_sources', sa.Column('schedule_time', sa.String(length=10), nullable=True))
    op.add_column('web_scraping_sources', sa.Column('schedule_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('web_scraping_sources', sa.Column('next_scheduled_run', sa.DateTime(), nullable=True))
    
    # Add index for scheduling
    op.create_index('idx_web_sources_schedule', 'web_scraping_sources', ['schedule_enabled', 'next_scheduled_run'])
    
    # Create scraping_jobs table
    op.create_table(
        'scraping_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('documents_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_matched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_new', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('triggered_by', sa.String(length=20), nullable=False),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['web_scraping_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_scraping_jobs_source_status', 'scraping_jobs', ['source_id', 'status'])
    op.create_index('idx_scraping_jobs_created', 'scraping_jobs', ['created_at'])
    
    # Create scraped_document_tracker table
    op.create_table(
        'scraped_document_tracker',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_url', sa.String(length=1000), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('first_scraped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['web_scraping_sources.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_url')
    )
    op.create_index('idx_tracker_url', 'scraped_document_tracker', ['document_url'])
    op.create_index('idx_tracker_hash', 'scraped_document_tracker', ['content_hash'])
    op.create_index('idx_tracker_source', 'scraped_document_tracker', ['source_id'])
    
    # Create source_health_metrics table
    op.create_table(
        'source_health_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('total_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),
        sa.Column('average_execution_time', sa.Integer(), nullable=True),
        sa.Column('total_documents_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_documents_per_run', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['web_scraping_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id')
    )
    op.create_index('idx_health_metrics_source', 'source_health_metrics', ['source_id'])
    op.create_index('idx_health_metrics_failures', 'source_health_metrics', ['consecutive_failures'])


def downgrade():
    # Drop new tables
    op.drop_table('source_health_metrics')
    op.drop_table('scraped_document_tracker')
    op.drop_table('scraping_jobs')
    
    # Remove new columns from web_scraping_sources
    op.drop_index('idx_web_sources_schedule', table_name='web_scraping_sources')
    op.drop_column('web_scraping_sources', 'next_scheduled_run')
    op.drop_column('web_scraping_sources', 'schedule_enabled')
    op.drop_column('web_scraping_sources', 'schedule_time')
    op.drop_column('web_scraping_sources', 'schedule_type')
    op.drop_column('web_scraping_sources', 'max_pages')
    op.drop_column('web_scraping_sources', 'pagination_enabled')
