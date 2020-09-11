import inspect
from typing import List, Type

from django.db import models
from django.db.models.base import ModelBase

from sa2django.column_mappers import map_column


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
        if "Meta" in attrs:
            meta = attrs["Meta"]
            if hasattr(meta, "sa_model"):
                sa_model = meta.sa_model
                cls.sa_model = sa_model
                del meta.sa_model

                if not hasattr(meta, "db_table"):
                    # set table name from sa model, unless explicitly specified
                    meta.db_table = sa_model.__tablename__

                # make columns
                table = sa_model.__table__
                for col in table.columns:
                    attrs[col.name] = map_column(col)

                # TODO extract columns
                # TODO keep track of created columns, and recreate of new sa_model is received
        return super().__new__(cls, name, bases, attrs, **kwargs)


class SA2DModel(models.Model, metaclass=SA2DBase):  # TODO
    class Meta:
        abstract = True
        managed = False
