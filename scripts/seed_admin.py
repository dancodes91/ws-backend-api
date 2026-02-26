"""Seed initial admin user. Run after create_tables."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Admin
from app.services.auth_service import hash_password

def main():
    db = SessionLocal()
    if db.query(Admin).first():
        print("Admin already exists. Skip seed.")
        db.close()
        return
    admin = Admin(
        name="Admin",
        email="admin@wallacedms.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)
    db.commit()
    print("Admin created: admin@wallacedms.com / admin123")
    db.close()

if __name__ == "__main__":
    main()
