from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# For SQLite, allow multiple threads to access the database
engine_kwargs = {"pool_pre_ping": True, "echo": settings.SQLALCHEMY_ECHO}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    logger.info(f"Using SQLite database: {settings.DATABASE_URL}")
else:
    logger.info("Using external database (PostgreSQL or other)")

try:
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

Base = declarative_base()