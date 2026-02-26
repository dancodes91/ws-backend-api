"""PriceFile model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PriceFile(Base):
    __tablename__ = "price_files"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    dealer_id = Column(Integer, ForeignKey("dealers.id", ondelete="CASCADE"), nullable=True)  # null = shared vendor file
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # path on disk
    version = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String(100), nullable=True)  # admin email or "wallace_utility"

    vendor = relationship("Vendor", back_populates="price_files")
    dealer = relationship("Dealer", backref="price_files")
    download_links = relationship("DownloadLink", back_populates="price_file")
