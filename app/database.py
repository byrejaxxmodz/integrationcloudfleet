import os

try:
    # Carga variables desde .env para entornos locales
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Si no está instalado python-dotenv, seguimos con variables de entorno del SO
    pass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_NAME = os.getenv("DB_NAME", "cloudfleet")
DB_USER = os.getenv("DB_USER", "mysql")
DB_PASS = os.getenv("DB_PASS", "mysql")

# Permitir override completo o fallback a SQLite sin tocar el código
DATABASE_URL_ENV = os.getenv("DATABASE_URL")
USE_SQLITE = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")
SQLITE_FILE = os.getenv("DB_SQLITE_FILE", "cloudfleet.db")

default_mysql_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

if USE_SQLITE and not DATABASE_URL_ENV:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_FILE}"
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL_ENV or default_mysql_url

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Handles disconnected connections
    pool_recycle=3600,   # Recycle connections every hour
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
