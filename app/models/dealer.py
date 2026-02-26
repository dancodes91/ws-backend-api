"""Dealer and DealerVendor models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Dealer(Base):
    __tablename__ = "dealers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    customer_number = Column(String(50), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vendors = relationship("DealerVendor", back_populates="dealer", cascade="all, delete-orphan")
    download_links = relationship("DownloadLink", back_populates="dealer")


class DealerVendor(Base):
    """Many-to-many: dealers can have multiple vendors with optional custom folder name."""
    __tablename__ = "dealer_vendors"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    custom_folder_name = Column(String(100), nullable=True)  # e.g. KEL_SILV, KEL_RHODE

    dealer = relationship("Dealer", back_populates="vendors")
    vendor = relationship("Vendor", back_populates="dealers")
