from app import get_db, Vendor, Payment, Receipt, DailyClosing # Adjust import based on your actual structure
from sqlalchemy import text

session = get_db()

try:
    # Delete data from tables in reverse order of dependencies if any
    session.query(DailyClosing).delete()
    session.query(Receipt).delete()
    session.query(Payment).delete()
    session.query(Vendor).delete()

    session.commit()
    print("Database cleared successfully.")
except Exception as e:
    session.rollback()
    print(f"An error occurred: {e}")
finally:
    session.close() 