from alembic import op
import sqlalchemy as sa

revision = "001_streams"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "streams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keitaro_campaign_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_stream_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("stream_type", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schema", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dirty", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_streams_keitaro_campaign_id", "streams", ["keitaro_campaign_id"])
    op.create_index("ix_streams_keitaro_stream_id", "streams", ["keitaro_stream_id"], unique=True)
    op.create_table(
        "stream_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stream_id", sa.Integer(), sa.ForeignKey("streams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("share", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("baseline_share", sa.Integer(), nullable=True),
        sa.Column("baseline_status", sa.String(length=16), nullable=False, server_default="absent"),
        sa.Column("baseline_pinned", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("stream_id", "offer_id", name="uq_stream_offer"),
    )
    op.create_index("ix_stream_offers_stream_id", "stream_offers", ["stream_id"])


def downgrade() -> None:
    op.drop_table("stream_offers")
    op.drop_table("streams")
