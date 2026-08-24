from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()

CVOR_STATUS = ("ACTIVE", "INACTIVE", "FAULT", "STANDBY", "MAINTENANCE")


class AirForceBase(Base):
    __tablename__ = "air_force_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cvor_systems: Mapped[list["CVORSystem"]] = relationship(
        "CVORSystem",
        back_populates="base",
        cascade="all, delete-orphan",
    )
    shelter_layouts: Mapped[list["ShelterLayout"]] = relationship(
        "ShelterLayout",
        back_populates="base",
        cascade="all, delete-orphan",
    )
    child_splits: Mapped[list["BaseSplit"]] = relationship(
        "BaseSplit",
        foreign_keys="BaseSplit.child_base_id",
        back_populates="child_base",
    )
    parent_splits: Mapped[list["BaseSplit"]] = relationship(
        "BaseSplit",
        foreign_keys="BaseSplit.parent_base_id",
        back_populates="parent_base",
    )


class CVORSystem(Base):
    __tablename__ = "cvor_systems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_id: Mapped[int] = mapped_column(ForeignKey("air_force_bases.id"), nullable=False)
    system_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency_mhz: Mapped[float] = mapped_column(Float, nullable=False)
    morse_id: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*CVOR_STATUS, name="cvor_status", native_enum=False),
        default="INACTIVE",
        nullable=False,
    )
    last_polled: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    base: Mapped["AirForceBase"] = relationship("AirForceBase", back_populates="cvor_systems")
    config_files: Mapped[list["CVORConfigFile"]] = relationship(
        "CVORConfigFile",
        back_populates="cvor",
        cascade="all, delete-orphan",
    )
    settings_history: Mapped[list["SettingsHistory"]] = relationship(
        "SettingsHistory",
        back_populates="cvor",
        cascade="all, delete-orphan",
    )


class ShelterLayout(Base):
    __tablename__ = "shelter_layouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_id: Mapped[int] = mapped_column(ForeignKey("air_force_bases.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shelter_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    layout_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    base: Mapped["AirForceBase"] = relationship("AirForceBase", back_populates="shelter_layouts")


class CVORConfigFile(Base):
    __tablename__ = "cvor_config_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cvor_id: Mapped[int] = mapped_column(ForeignKey("cvor_systems.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cvor: Mapped["CVORSystem"] = relationship("CVORSystem", back_populates="config_files")


class SettingsHistory(Base):
    __tablename__ = "settings_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cvor_id: Mapped[int] = mapped_column(ForeignKey("cvor_systems.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cvor: Mapped["CVORSystem"] = relationship("CVORSystem", back_populates="settings_history")


class BaseSplit(Base):
    __tablename__ = "base_splits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_base_id: Mapped[int] = mapped_column(ForeignKey("air_force_bases.id"), nullable=False)
    child_base_id: Mapped[int] = mapped_column(ForeignKey("air_force_bases.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    split_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    parent_base: Mapped["AirForceBase"] = relationship(
        "AirForceBase",
        foreign_keys=[parent_base_id],
        back_populates="parent_splits",
    )
    child_base: Mapped["AirForceBase"] = relationship(
        "AirForceBase",
        foreign_keys=[child_base_id],
        back_populates="child_splits",
    )
