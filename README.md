# SqlAlchemy to Django Bridge

Convert sqlalchemy database schemas to django database models at runtime.

Original url: [https://github.com/mariushelf/sa2django](https://github.com/mariushelf/sa2django)


The SQLAlchemy to Django Bridge allows to specify your data models in SQLAlchemy
and use them in Django, without manually re-specifying all your models and fields
for the Django ORM.


# Why did you create this package?

Specifying a schema in SQLAlchemy and then using it in Django sounds like... counter-
intuitive. There are a lot of *Why nots* to answer...


## Why not specify your models in Django straight away?

We use Django to serve data that is maintained from sources outside of the Django
application. Those sources already specify a complete SQLAlchemy model.

Hence we already have a full specification of the data model in SQLAlchemy.


## Why not simply use `inspectdb` to dynamically generate the Django model specifications?

[inspectdb](https://docs.djangoproject.com/en/3.1/howto/legacy-databases/) is not
that dynamic after all -- it generates a Python file once, which needs to be manually
tweaked. And each time the data model changes, you need to adjust that Python file.

Also it is often not possible to automatically derive all relations between models
from the database. With third-party datasources, often relations are not manifested
as foreign key constraints in the database schema, but just in some documentation
that explains the relations in human-, but not machine-readable form.

Our SQLAlchemy models already contain all those relations, and it makes sense to
convert the SQLAlchemy models to Django ORM *at runtime*.


# Status

The SQLAlchemy to Django Bridge works well for our use case.

There are probably a lot of corner cases and advanced (or not so advanced) features
of SQLAlchemy that are not (yet) supported.


# Installation

`pip install sa2django`


# Features

* basic data types (int, float, string, varchar, char, date, datetime etc, bytea)
* foreign keys and many-to-one relationships
* many-to-many relationships including `through` tables
* automatic inference of all declared models in a sqlalchemy `Base`
* alternatively define your Django models as usual, but use the `SA2DModel` as
  base class. Then all database fields are added from the corresponding sqlalchemy
  model, but you can still add properties and functions to the Django model


# Limitations

SQLAlchemy provides a superset of Django's functionality. For this reason, there's a
long list of limitations.

The list is even longer and probably not exhaustive because sa2django is a young project
tailored to its author's current needs.

* at the moment only declarative base definitions are supported, no pure `Mapper`
  objects
* composite foreign keys and primary keys are not supported. Primary keys and foreign
  keys must contain exactly one column
  

## Many to many relationships

* In sqlalchemy, in the mapper of the intermediate table, both foreign keys *and*
  relationships linking to both tables must be specified.
  
  Example:
  ```python
  class CarParentAssoc(Base):
      __tablename__ = "cartoparent"
      id = Column(Integer, primary_key=True)
      car = relationship("Car")
      parent = relationship("Parent")
      car_id = Column(Integer, ForeignKey("car.car_id"))
      parent_id = Column(Integer, ForeignKey("parent.id"))
  ```
  Note that for both links to the `car` and `parent` table, both foreign keys and
  relationship attributes are specified.


# Contributing

Pull requests are more than welcome! Ideally reach out to us by creating or replying
to a Github ticket such that we can align our work and ideas.


# License

[MIT](LICENSE)


Author: Marius Helf 
  ([helfsmarius@gmail.com](mailto:helfsmarius@gmail.com))
