from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# Use Database URL from env (for Supabase/Render) or fallback to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

# PostgreSQL requires different args than SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)  # The original text from the user
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration_days = Column(Integer)
    effort_level = Column(String) # High, Medium, Low (Inferred by Gemma)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to reminders
    reminders = relationship("Reminder", back_populates="task")

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    reminder_time = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    message_type = Column(String) # e.g., "Early Check-in", "Final Warning"

    task = relationship("Task", back_populates="reminders")

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
