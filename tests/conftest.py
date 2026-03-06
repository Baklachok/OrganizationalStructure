from __future__ import annotations

from collections.abc import Generator

import pytest
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def engine() -> Generator[Engine, None, None]:
    test_engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(engine: Engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with testing_session_local() as session:
        yield session
