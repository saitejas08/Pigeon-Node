from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from web3 import Web3
import os
import secrets

# --- UPDATED DATABASE CONNECTION WITH POOLING ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:thesis2026@postgres-vault:5432/pigeondb")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Keep 20 connections open to be reused
    max_overflow=10,       # Allow 10 extra connections during bursts
    pool_timeout=30,       # Wait 30 seconds before timing out
    pool_recycle=1800,     # Refresh connections every 30 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Intercept(Base):
    __tablename__ = "intercepts"
    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, index=True)
    commitment = Column(String)
    salt = Column(String)
    timestamp = Column(Float)
    node_id = Column(String)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Pigeon Command Center")

class Payload(BaseModel):
    tx_hash: str
    raw_ip: str
    timestamp: float
    node_id: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/ingest")
def ingest_data(payload: Payload, db: Session = Depends(get_db)):
    # 1. Generate a 32-byte random cryptographic salt
    salt = secrets.token_hex(32)

    # 2. Cryptographic Commitment -> keccak256(IP + Salt)
    data_to_hash = payload.raw_ip + salt
    commitment = Web3.keccak(text=data_to_hash).hex()

    # 3. Store in Vault (Raw IP is never saved)
    new_intercept = Intercept(
        tx_hash=payload.tx_hash,
        commitment=commitment,
        salt=salt,
        timestamp=payload.timestamp,
        node_id=payload.node_id
    )
    db.add(new_intercept)
    db.commit()

    return {"status": "success", "tx_hash": payload.tx_hash, "commitment": commitment}
