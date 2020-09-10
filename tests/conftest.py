import django
import pytest


@pytest.fixture(scope="function")
def django_db_setup(django_db_blocker):
    """ Prevent creation of a test db (because we do that with sqlalchemy) """
    yield

    with django_db_blocker.unblock():
        django.db.connections.close_all()
