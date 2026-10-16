"""add retry tracking and enforce one delivery per wish

Revision ID: 62eed6e615bf
Revises: 1e909c548b88
Create Date: 2026-10-11 08:59:42.669931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62eed6e615bf'
down_revision = '1e909c548b88'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Resolve duplicates before running:
    # SELECT wish_id, COUNT(*) FROM deliveries GROUP BY wish_id HAVING COUNT(*) > 1;
    op.add_column("deliveries", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("deliveries", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deliveries", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_deliveries_wish_id", "deliveries", ["wish_id"])
    op.execute(
        "ALTER TABLE deliveries MODIFY status "
        "ENUM('PENDING','SENDING','SENT','FAILED') NOT NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE deliveries MODIFY status ENUM('PENDING','SENT','FAILED') NOT NULL")
    op.drop_constraint("uq_deliveries_wish_id", "deliveries", type_="unique")
    op.drop_column("deliveries", "next_attempt_at")
    op.drop_column("deliveries", "last_attempt_at")
    op.drop_column("deliveries", "attempt_count")
