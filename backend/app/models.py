from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    keitaro_campaign_id: Mapped[int] = mapped_column(Integer, index=True)
    keitaro_stream_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    stream_type: Mapped[str] = mapped_column(String(32), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    schema_name: Mapped[str] = mapped_column("schema", String(32), default="")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    dirty: Mapped[bool] = mapped_column(Boolean, default=False)
    offers: Mapped[list["StreamOffer"]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan",
    )


class StreamOffer(Base):
    __tablename__ = "stream_offers"
    __table_args__ = (UniqueConstraint("stream_id", "offer_id", name="uq_stream_offer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stream_id: Mapped[int] = mapped_column(ForeignKey("streams.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(512), default="")
    share: Mapped[int] = mapped_column(Integer, default=0)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="active")
    baseline_share: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_status: Mapped[str] = mapped_column(String(16), default="absent")
    baseline_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    stream: Mapped[Stream] = relationship(back_populates="offers")
