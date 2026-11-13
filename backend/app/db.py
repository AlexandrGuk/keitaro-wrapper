from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def prepare_database_url(url: str) -> str:
    if not url.startswith("sqlite"):
        return url
    path = Path(url.split("sqlite:///", 1)[1])
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[1] / path).resolve()
        url = f"sqlite:///{path.as_posix()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    return url


engine = create_engine(
    prepare_database_url(settings.sqlalchemy_url),
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_sqlite_fk(dbapi_connection, _record) -> None:
    if engine.dialect.name != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False)
