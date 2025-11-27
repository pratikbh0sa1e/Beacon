from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Construct DATABASE_URL from individual components
DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String)
    file_path = Column(String)
    s3_url = Column(String)
    extracted_text = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(Text, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
