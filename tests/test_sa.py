import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests.testsite.testapp.models as dm
from tests.sa_models import Base, Car, Child, Parent


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
    parent = Parent(name="Peter")
    parent2 = Parent(name="Hugo")
    child1 = Child(name="Hans", age=3, parent=parent, boolfield=True)
    child2 = Child(name="Franz", age=5, parent=parent, boolfield=False)
    car1 = Car(horsepower=560)
    car2 = Car(horsepower=32)
    parent.cars = [car1, car2]
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


def test_nullable(mock_data_session):
    print(dm.Child.boolfield)
    assert dm.Child._meta.get_field("boolfield").null == False
    assert dm.Child._meta.get_field("citextfield").null == True


@pytest.mark.django_db
def test_fk(mock_data_session):
    parent = dm.Parent.objects.get(name="Peter")
    dm_child = dm.Child.objects.get(name="Hans")
    assert dm_child.parent_id == parent.id
    assert dm_child.parent == parent

    # test back reference
    assert len(parent.children.all()) == 2
    assert dm_child in parent.children.all()


@pytest.mark.django_db
def test_pk(mock_data_session):
    assert dm.Child._meta.pk.name == "key"
    assert dm.Parent._meta.pk.name == "id"


@pytest.mark.django_db
def test_many_to_many(mock_data_session):

    meta = dm.Child._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.CarParentAssoc._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.Parent._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    meta = dm.Car._meta
    print()
    print(f"{meta=}")
    for field in meta.get_fields():
        print(f"{field.name=}; {meta.get_field(field.name)}")

    peter = dm.Parent.objects.get(name="Peter")
    assert len(peter.cars.all()) == 2

    car0 = dm.Car.objects.all()[0]
    assert car0.drivers.all()[0].name == "Peter"

    car1 = dm.Car.objects.all()[1]
    assert car1.drivers.all()[0].name == "Peter"
