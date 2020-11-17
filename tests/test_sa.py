import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests.testsite.testapp.models as dm
from tests.sa_models import Base, SACar, SAChild, SAParent


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
    print(f"{Base.metadata.tables.keys()=}")
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(scope="session")
def mock_data_session(session):
    parent = SAParent(name="Peter")
    parent2 = SAParent(name="Hugo")
    child1 = SAChild(name="Hans", age=3, parent=parent, boolfield=True)
    child2 = SAChild(name="Franz", age=5, parent=parent, boolfield=False)
    car1 = SACar(horsepower=560)
    car2 = SACar(horsepower=32)
    parent.cars = [car1, car2]
    session.add_all([parent, parent2, child1, child2])
    session.commit()
    return session


def test_data(mock_data_session):
    assert len(mock_data_session.query(SAParent).all()) == 2
    assert len(mock_data_session.query(SAChild).all()) == 2


@pytest.mark.django_db
def test_django_orm(mock_data_session):
    parents = dm.DMParent.objects.order_by("pk")
    assert len(parents) == 2
    assert parents[0].name == "Peter"
    assert parents[1].name == "Hugo"


def test_nullable(mock_data_session):
    print(dm.DMChild.boolfield)
    assert dm.DMChild._meta.get_field("boolfield").null == False
    assert dm.DMChild._meta.get_field("citextfield").null == True


@pytest.mark.django_db
def test_fk(mock_data_session):
    parent = dm.DMParent.objects.get(name="Peter")
    dm_child = dm.DMChild.objects.get(name="Hans")
    assert dm_child.parent_id == parent.id
    assert dm_child.parent == parent

    # test back reference
    assert len(parent.children.all()) == 2
    assert dm_child in parent.children.all()


@pytest.mark.django_db
def test_pk(mock_data_session):
    assert dm.DMChild._meta.pk.name == "key"
    assert dm.DMParent._meta.pk.name == "id"


@pytest.mark.django_db
def test_many_to_many(mock_data_session):

    meta = dm.DMChild._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.DMCarParentAssoc._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.DMParent._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.DMCar._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    peter = dm.DMParent.objects.get(name="Peter")
    assert len(peter.cars.all()) == 2

    car0 = dm.DMCar.objects.all()[0]
    assert car0.drivers.all()[0].name == "Peter"

    car1 = dm.DMCar.objects.all()[1]
    assert car1.drivers.all()[0].name == "Peter"
