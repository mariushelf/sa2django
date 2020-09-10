import inspect
from typing import List, Type

from django.db import models
from django.db.models.base import ModelBase


def extract_tables(module):
    tables: List[Type] = []
    for name, cls in inspect.getmembers(module):
        try:
            if issubclass(cls, module.Base) and "__table__" in cls.__dict__:
                tables.append(cls)
        except (AttributeError, TypeError):
            continue
    return tables


class SA2DBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        attrs["id"] = models.IntegerField(primary_key=True)
        attrs["name"] = models.CharField(max_length=100)
        return super().__new__(cls, name, bases, attrs, **kwargs)


class SA2DModel(models.Model, metaclass=SA2DBase):
    class Meta:
        abstract = True
        managed = False
