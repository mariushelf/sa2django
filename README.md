# SqlAlchemy to Django Bridge

Convert sqlalchemy database schemas to django database models at runtime.

Original url: [https://github.com/mariushelf/sa2django](https://github.com/mariushelf/sa2django)


The SQLAlchemy to Django Bridge allows to specify your data models in SQLAlchemy
and use them in Django, without manually re-specifying all your models and fields
for the Django ORM.


# Why this package?

Specifying a schema in SQLAlchemy and then using it in Django sounds like... counter-
intuitive. There are a lot of *Why nots* to answer...


## Why not specify your models in Django straight away?

Sometimes some or all of the data you serve from Django is maintained or created
by sources that are not part of the Django application. If those sources already specify
a complete SQLAlchemy model, then the SQLAlchemy to Django bridge is useful.


## Why not simply use `inspectdb` to dynamically generate the Django model specifications?

[inspectdb](https://docs.djangoproject.com/en/3.1/howto/legacy-databases/) is not
that dynamic after all -- it generates a Python file once, which needs to be manually
tweaked. And each time the data model changes, you need to adjust that Python file.

Also it is often not possible to automatically derive all relations between models
from the database. With third-party datasources, often relations are not manifested
as foreign key constraints in the database schema, but just in some documentation
that explains the relations in human-, but not machine-readable form.

If the SQLAlchemy models already contain all those relations then it makes sense to
convert the SQLAlchemy models to Django ORM *at runtime*.


# Status

The SQLAlchemy to Django Bridge works well for the author's use case.

There are probably a lot of corner cases and advanced (or not so advanced) features
of SQLAlchemy that are not (yet) supported.

The tests run in sqlite, and our production system uses PostgreSQL.
It may or may not work with other database systems.


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
  
# Usage

## Define your SQLAlchemy schema
Say you have the following SQLAlchemy schema:

```python
# sqlalchemy_schema.py
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("Child", back_populates="parent")


class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    parent_id = Column(Integer, ForeignKey("parent.id"))
    parent = relationship(Parent, uselist=False, back_populates="children")
```


## Automatic inference
You can use it in your Django application by simply adding the following code to
your `models.py`:

```python
# models.py
from sa2django.core import generate_sa2d_models, inject_models
from sqlalchemy_models import Base  # this is what we have specified in the snippet above

_models = generate_sa2d_models(Base, __name__)
inject_models(_models, globals())
```

This will add the classes `Child` and `Parent` to your `models` module.
These classes are the Django models that correspond to the SQLAlchemy models.

You can't see it in the file, but Django will recognize them, and you can import them
anywhere in the application as if you had declared them manually:

```python
from models import Parent, Child

print(Child.objects.all())
child = Child.objects.get(pk=my_pk)
print(child.parents.all())
```

*Note:* your IDE might complain because it thinks that `Parent` and `Child` do not
exist. It can't know, because the classes are created at runtime. The code will work
fine.


## Manual specification and custom properties

A strength of Django is that it allows to specify additional properties on a model.
sa2django supports this. To do so you can declare your models explicitly and inherit
from `sa2django.SA2DModel` instead of `django.db.models.Model`, and specify the
corresponding SQLAlchemy model in the `Meta` class under the `sa_model` attribute.

You also need to register *all* Django models that are referenced by any model in the
SQLAlchemy schema with `register_table()`.

Then you have control over the class name and additional properties and use `sa2django`
only to add all fields and relations to your Django model.


Here's and example:
```python
from sa2django import register_table, SA2DModel
from sa2django.core import extract_tables_from_base
import sqlalchemy_models

# extract all SQLAlchemy tables
_tables = extract_tables_from_base(sqlalchemy_models.Base)

# register the tables
for _tablename, _sa_class in _tables.items():
    register_table(_tablename, _sa_class.__name__)

class Child(SA2DModel):
    class Meta:
        sa_model = sqlalchemy_models.Child
        ordering = ["age"]
    
    @property
    def age_next_year(self):
        return self.age + 1

class Parent(SA2DModel):
    class Meta:
        sa_model = sqlalchemy_models.Parent
```

At the moment it is not possible to mix manual and automatic model extraction --
if you specify one model manually, you cannot use `generate_sa2d_models()` anymore,
so you need to specify *all* models manually.


# Limitations

SQLAlchemy provides a superset of Django's functionality. For this reason, there's a
long list of limitations.

The list is even longer and probably not exhaustive because sa2django is a young project
tailored to its author's current needs.

* at the moment only declarative base definitions are supported, no pure `Mapper`
  objects
* composite foreign keys and primary keys are not supported. Primary keys and foreign
  keys must contain exactly one column
* relations that do not use a foreign key are not added to the Django models
  

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


# Changelog
## 0.1.3
- set arbitrary `max_length` of 2048 on String fields that do not have a defined length
  in sqlalchemy. Necessary because Django does not support unlimited String fields, even
  though some backends (e.g., Postgres) do


# Contributing

Pull requests are more than welcome! Ideally reach out to us by creating or replying
to a Github ticket such that we can align our work and ideas.


# License

[MIT](LICENSE)


Author: Marius Helf 
  ([helfsmarius@gmail.com](mailto:helfsmarius@gmail.com))
