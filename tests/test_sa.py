import sqlite3
from typing import Type

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

import tests.testsite.testapp.models as dm

Base: Type = declarative_base()


class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    parent_id = Column(Integer, ForeignKey("parent.id"))
    parent = relationship(Parent, uselist=False)


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
    parent = Parent(name="Peter")
    parent2 = Parent(name="Hugo")
    child1 = Child(name="Hans", age=3, parent=parent)
    child2 = Child(name="Franz", age=5, parent=parent)
    session.add_all([parent, parent2, child1, child2])
    session.commit()
    return session


def test_data(mock_data_session):
    assert len(mock_data_session.query(Parent).all()) == 2
    assert len(mock_data_session.query(Child).all()) == 2


@pytest.mark.django_db
def test_django_orm(mock_data_session):
    parents = dm.Parent.objects.order_by("pk")
    assert len(parents) == 2
    assert parents[0].name == "Peter"
    assert parents[1].name == "Hugo"
