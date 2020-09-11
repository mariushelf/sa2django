import inspect
import logging
from typing import Dict, List, Type

import sqlalchemy as sa
from django.db import models as dm
from django.db.models.base import ModelBase
from sqlalchemy.util import symbol

from sa2django.column_mappers import map_column

logger = logging.getLogger(__name__)


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
    table_mapping = {}

    @classmethod
    def register_table(cls, tablename: str, dm_model_name: str):
        cls.table_mapping[tablename] = dm_model_name

    def __new__(cls, name, bases, attrs, **kwargs):
        attrs["id"] = dm.IntegerField(primary_key=True)
        attrs["name"] = dm.CharField(max_length=100)
        if "Meta" in attrs:
            meta = attrs["Meta"]
            if hasattr(meta, "sa_model"):
                sa_model = meta.sa_model
                cls.sa_model = sa_model
                del meta.sa_model

                if not hasattr(meta, "db_table"):
                    # set table name from sa model, unless explicitly specified
                    meta.db_table = sa_model.__tablename__

                cls.register_table(meta.db_table, name)

                ins = sa.inspect(sa_model)

                # make foreign keys
                fks = cls.foreign_keys(ins)
                attrs.update(fks)
                fk_names = {fk.db_column for fk in fks.values()}

                # make columns
                for col in ins.columns:
                    if col.name in fk_names:
                        continue
                    attrs[col.name] = map_column(col)

                # TODO keep track of created columns, and recreate of new sa_model is received
        return super().__new__(cls, name, bases, attrs, **kwargs)

    @classmethod
    def foreign_keys(cls, inspection) -> Dict[str, dm.ForeignKey]:
        fks = {}
        table_name = inspection.local_table.name
        for relation in inspection.relationships:
            if relation.direction != symbol("MANYTOONE"):
                continue
            name = relation.key
            related_name = relation.back_populates
            if len(relation.local_remote_pairs) > 1:
                logger.warning("Foreign key with more than one column. Skipping")
                continue
            pair = relation.local_remote_pairs[0]
            db_column = pair[0].name
            remote = pair[1]
            to_field = remote.name
            remote_table = remote.table.name
            if remote_table == table_name:
                to = "self"
            else:
                to = cls.table_mapping[remote_table]
            print(to, db_column, to_field, related_name)
            fks[name] = dm.ForeignKey(
                to,
                on_delete=dm.CASCADE,
                db_column=db_column,
                to_field=to_field,
                related_name=related_name,
            )
        return fks


class SA2DModel(dm.Model, metaclass=SA2DBase):
    class Meta:
        abstract = True
        managed = False


def register_table(tablename: str, dm_model_name: str):
    SA2DBase.register_table(tablename, dm_model_name)
