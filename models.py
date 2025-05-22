from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Text, Boolean, func, extract, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime, date
import os

# Set up SQLAlchemy with SQLite
DATABASE_URL = 'sqlite:///market_management.db'
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_timeout=30)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Define models using SQLAlchemy
class Vendor(Base):
    __tablename__ = 'vendors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    shop_number = Column(String(50), nullable=False)
    block = Column(String(50), nullable=False)
    registration_date = Column(Date, default=datetime.utcnow().date)

    # Relationships
    payments = relationship('Payment', backref='vendor', lazy='dynamic')
    receipts = relationship('Receipt', backref='vendor', lazy='dynamic')

    # Constraint to prevent duplicate shop+block combinations
    __table_args__ = (UniqueConstraint('shop_number', 'block', name='unique_shop_block'),)

    def __repr__(self):
        return f'<Vendor {self.name} - Shop {self.shop_number}, Block {self.block}>'

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=True)
    amount = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    payment_type = Column(String(20), nullable=False)  # regular, arrears, advance
    date = Column(Date, default=datetime.utcnow().date)
    time = Column(String(8), default=datetime.utcnow().strftime('%H:%M:%S'))  # Store as HH:MM:SS
    daily_closing_id = Column(Integer, ForeignKey('daily_closings.id'), nullable=True)

    def __repr__(self):
        return f'<Payment ₦{self.amount} - Vendor ID: {self.vendor_id}, Type: {self.payment_type}>'

class Receipt(Base):
    __tablename__ = 'receipts'

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=True)
    issue_date = Column(Date, default=datetime.utcnow().date)
    amount = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    receipt_number = Column(String(50), unique=True, nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)

    # Create a relationship back to payment
    payment = relationship('Payment', backref='receipt', uselist=False)

    def __repr__(self):
        return f'<Receipt #{self.receipt_number} - ₦{self.amount}>'

class DailyClosing(Base):
    __tablename__ = 'daily_closings'

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.utcnow().date, unique=True)
    total_amount = Column(Float, nullable=False)
    regular_amount = Column(Float, default=0.0)
    arrears_amount = Column(Float, default=0.0)
    advance_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    is_closed = Column(Boolean, default=True)

    # Relationships
    payments = relationship('Payment', backref='daily_closing', lazy='dynamic')

    def __repr__(self):
        return f'<Daily Closing {self.date} - ₦{self.total_amount}>'

# Function to get DB session - used by page modules
def get_db():
    return db_session

# Create database tables if the script is run directly
if __name__ == '__main__':
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.") 