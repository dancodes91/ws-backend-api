"""Seed sample vendors (KEL_SILV, YAMAHA, etc.). Run after create_tables."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Vendor

SAMPLE_VENDORS = [
    {"code": "KEL_SILV", "name": "Kellogg Silver Cloud", "description": "Dealer-specific"},
    {"code": "KEL_RHODE", "name": "Kellogg Rhode River", "description": "Dealer-specific"},
    {"code": "YAMAHA", "name": "Yamaha", "description": "Manufacturer"},
    {"code": "MERCURY", "name": "Mercury", "description": "Manufacturer"},
]


def main():
    db = SessionLocal()
    for v in SAMPLE_VENDORS:
        if db.query(Vendor).filter(Vendor.code == v["code"]).first():
            continue
        db.add(Vendor(**v))
    db.commit()
    print("Vendors seeded.")
    db.close()


if __name__ == "__main__":
    main()
