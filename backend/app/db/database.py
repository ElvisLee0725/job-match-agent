from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.models import Base


def make_engine(database_path: str):
    connect_args = {"check_same_thread": False} if database_path != ":memory:" else {"check_same_thread": False}
    engine = create_engine(f"sqlite:///{database_path}", connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine


engine = make_engine(str(settings.database_path))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
