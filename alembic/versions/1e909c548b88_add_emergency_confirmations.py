"""add emergency confirmations

Revision ID: 1e909c548b88
Revises: 353163d4625c
Create Date: 2026-10-10 14:27:22.717378

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e909c548b88'
down_revision = '353163d4625c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "emergency_confirmations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("checkin_event_id", sa.String(length=36), nullable=False),
        sa.Column("emergency_contact_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["checkin_event_id"],
            ["checkin_events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["emergency_contact_id"],
            ["emergency_contacts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("checkin_event_id"),
        sa.UniqueConstraint("token_hash"),
    )

    op.create_index(
        "ix_emergency_confirmations_checkin_event_id",
        "emergency_confirmations",
        ["checkin_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_emergency_confirmations_emergency_contact_id",
        "emergency_confirmations",
        ["emergency_contact_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_emergency_confirmations_token_hash",
        table_name="emergency_confirmations",
    )
    op.drop_index(
        "ix_emergency_confirmations_emergency_contact_id",
        table_name="emergency_confirmations",
    )
    op.drop_index(
        "ix_emergency_confirmations_checkin_event_id",
        table_name="emergency_confirmations",
    )
    op.drop_table("emergency_confirmations")