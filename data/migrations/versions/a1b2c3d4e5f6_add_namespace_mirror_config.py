"""add namespace mirror config

Revision ID: a1b2c3d4e5f6
Revises: fc47c1ec019f
Create Date: 2025-12-01 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7078c84d14e8'

from alembic import op
import sqlalchemy as sa

def upgrade(op, tables, tester):
    op.create_table(
        'namespacemirrorconfig',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('creation_date', sa.DateTime(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('external_registry', sa.String(length=255), nullable=False),
        sa.Column('external_namespace', sa.String(length=255), nullable=False),
        sa.Column('external_registry_username', sa.String(length=4096), nullable=True),
        sa.Column('external_registry_password', sa.String(length=9000), nullable=True),
        sa.Column('sync_interval', sa.Integer(), nullable=False, server_default='86400'),
        sa.Column('sync_start_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('sync_status', sa.String(length=255), nullable=False, server_default='never_run'),
        sa.Column('sync_message', sa.Text(), nullable=True),
        sa.Column('last_sync_start', sa.DateTime(), nullable=True),
        sa.Column('repo_filter_type', sa.String(length=255), nullable=False, server_default='regex'),
        sa.Column('repo_filter_value', sa.String(length=255), nullable=True),
        sa.Column('internal_robot_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['user.id'], name=op.f('fk_namespacemirrorconfig_organization_id_user')),
        sa.ForeignKeyConstraint(['internal_robot_id'], ['user.id'], name=op.f('fk_namespacemirrorconfig_internal_robot_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_namespacemirrorconfig'))
    )
    op.create_index(op.f('ix_namespacemirrorconfig_organization_id'), 'namespacemirrorconfig', ['organization_id'], unique=True)
    op.create_index(op.f('ix_namespacemirrorconfig_internal_robot_id'), 'namespacemirrorconfig', ['internal_robot_id'], unique=False)

def downgrade(op, tables, tester):
    op.drop_table('namespacemirrorconfig')

