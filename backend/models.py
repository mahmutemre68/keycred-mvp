import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    receipts = relationship("BankReceipt", back_populates="tenant")
    scores = relationship("Score", back_populates="tenant")


class BankReceipt(Base):
    __tablename__ = "bank_receipts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="receipts")
    score = relationship("Score", back_populates="receipt", uselist=False)


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    receipt_id = Column(Integer, ForeignKey("bank_receipts.id"), nullable=False)
    keycred_score = Column(Float, nullable=False)
    max_rent_limit = Column(Float, nullable=False)
    scored_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="scores")
    receipt = relationship("BankReceipt", back_populates="score")
