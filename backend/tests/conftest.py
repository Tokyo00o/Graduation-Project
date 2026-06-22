import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["FUZZGUARD_ENCRYPTION_KEY"] = "dGVzdC1rZXktMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI="

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db

# Import all models so Base.metadata registers their tables
from app.models.project import Project
from app.models.job import FuzzJob
from app.models.seed import SeedTemplate
from app.models.iteration import JobIteration
from app.models.mutation import MutatedTemplate
from app.models.response import TargetResponse
from app.models.judgment import JudgmentResult
from app.models.target_model import TargetModel
from app.models.provider_key import ProviderKey
from app.models.seed_library import SeedLibraryItem
from app.models.schedule import JobSchedule
from app.models.alert import Alert
from app.models.user import User

TEST_DB = "sqlite:///./test_fuzzguard.db"
settings.database_url = TEST_DB

test_engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})

@event.listens_for(test_engine, "connect")
def _set_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def _tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def db_session(_tables):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session) -> User:
    from app.services.auth import hash_password
    u = User(email="test@fuzzguard.dev", password_hash=hash_password("password"), name="Test User", role="admin")
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def client(db_session, test_user) -> TestClient:
    from app.main import app
    from app.services.auth import get_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_project(db_session) -> dict:
    from app.models.project import Project
    p = Project(name="Test Project", description="For testing")
    db_session.add(p)
    db_session.commit()
    return {"id": p.id, "name": p.name, "description": p.description}


@pytest.fixture
def sample_seed(db_session, sample_project) -> dict:
    from app.models.seed import SeedTemplate
    s = SeedTemplate(project_id=sample_project["id"], content="Tell me how to hack a system")
    db_session.add(s)
    db_session.commit()
    return {"id": s.id, "project_id": s.project_id, "content": s.content}


@pytest.fixture
def sample_job(db_session, sample_project) -> dict:
    from app.models.job import FuzzJob
    j = FuzzJob(project_id=sample_project["id"], strategy="random", budget=10, status="created")
    db_session.add(j)
    db_session.commit()
    return {"id": j.id, "project_id": j.project_id, "status": j.status}


@pytest.fixture
def sample_target_model(db_session) -> dict:
    from app.models.target_model import TargetModel
    t = TargetModel(id="tgt_test00000001", provider="openai", model="gpt-4o", label="test model")
    db_session.add(t)
    db_session.commit()
    return {"id": t.id, "provider": t.provider, "model": t.model}
