import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests.testsite.testapp.models as dm
from tests.sa_models import Base, SAChild, SAParent


@pytest.fixture(scope="session")
def engine():
    print("NEW ENGINE")
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(
            "file:memorydb?mode=memory&cache=shared", uri=True
        ),
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session(engine):
    print("CREATE TABLES")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(scope="session")
def mock_data_session(session):
    parent = SAParent(name="Peter")
    parent2 = SAParent(name="Hugo")
    child1 = SAChild(name="Hans", age=3, parent=parent)
    child2 = SAChild(name="Franz", age=5, parent=parent)
    session.add_all([parent, parent2, child1, child2])
    session.commit()
    return session


# @pytest.fixture(scope="session")
# def parent_without_child(session):


def test_data(mock_data_session):
    assert len(mock_data_session.query(SAParent).all()) == 2
    assert len(mock_data_session.query(SAChild).all()) == 2


@pytest.mark.django_db
def test_django_orm(mock_data_session):
    parents = dm.DMParent.objects.order_by("pk")
    assert len(parents) == 2
    assert parents[0].name == "Peter"
    assert parents[1].name == "Hugo"


@pytest.mark.django_db
def test_one_to_one_fk(mock_data_session):
    parent = dm.DMParent.objects.get(name="Peter")
    dm_child = dm.DMChild.objects.get(name="Hans")
    assert dm_child.parent_id == parent.id
    assert dm_child.parent == parent