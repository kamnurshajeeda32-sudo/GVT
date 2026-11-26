from alembic import op
import sqlalchemy as sa
revision="0001"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("users",sa.Column("id",sa.String(36),primary_key=True),sa.Column("email",sa.String(254),nullable=False,unique=True),sa.Column("password_hash",sa.String(512),nullable=False),sa.Column("name",sa.String(100),nullable=False),sa.Column("role",sa.String(32),nullable=False),sa.Column("verified",sa.Boolean(),nullable=False))
    op.create_table("auth_tokens",sa.Column("digest",sa.String(64),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("purpose",sa.String(20),nullable=False),sa.Column("expires",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_auth_tokens_user_id","auth_tokens",["user_id"])
def downgrade():
    op.drop_table("auth_tokens")
    op.drop_table("users")
