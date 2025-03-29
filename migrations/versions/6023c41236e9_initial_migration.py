"""Initial Migration

Revision ID: 6023c41236e9
Revises: 
Create Date: 2025-03-29 02:49:14.811552

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6023c41236e9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Department',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('location', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('Role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('Employee',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_number', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('dept_id', sa.Integer(), nullable=True),
    sa.Column('date_joined', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['dept_id'], ['Department.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['Role.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('employee_number')
    )
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_Employee_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_Employee_username'), ['username'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_Employee_username'))
        batch_op.drop_index(batch_op.f('ix_Employee_email'))

    op.drop_table('Employee')
    op.drop_table('Role')
    op.drop_table('Department')
    # ### end Alembic commands ###
