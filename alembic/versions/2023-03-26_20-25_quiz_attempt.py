"""quiz attempt

Revision ID: 14780a46f085
Revises: 8fed53710991
Create Date: 2023-03-26 20:25:00.310926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14780a46f085'
down_revision = '8fed53710991'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('attempts',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('questions', sa.Integer(), nullable=False),
    sa.Column('correct_answers', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attempts_id'), 'attempts', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_attempts_id'), table_name='attempts')
    op.drop_table('attempts')
    # ### end Alembic commands ###
