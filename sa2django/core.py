import inspect
import logging
from typing import Any, Dict, List, Type

import sqlalchemy as sa
from django.db import models as dm
from django.db.models.base import ModelBase
from sqlalchemy import Column
from sqlalchemy.orm import Mapper, RelationshipProperty
from sqlalchemy.util import symbol
from sqlalchemy_utils import get_mapper

from sa2django.column_mappers import map_column

logger = logging.getLogger(__name__)


def extract_tables_from_module(module):
    tables: List[Type] = []
    for name, cls in inspect.getmembers(module):
        try:
            if issubclass(cls, module.Base) and "__table__" in cls.__dict__:
                tables.append(cls)
        except (AttributeError, TypeError):
            continue
    return tables


class SA2DjangoException(Exception):
    pass


class SA2DBase(ModelBase):
    table_mapping = {}
    related_fields = set()

    @classmethod
    def register_table(cls, tablename: str, dm_model_name: str):
        cls.table_mapping[tablename] = dm_model_name

    def __new__(cls, name, bases, attrs, **kwargs):
        if "Meta" in attrs:
            meta = attrs["Meta"]
            if hasattr(meta, "sa_model"):
                sa_model = meta.sa_model
                cls.sa_model = sa_model
                del meta.sa_model

                if not hasattr(meta, "db_table"):
                    # set table name from sa model, unless explicitly specified
                    meta.db_table = sa_model.__tablename__

                logger.debug(
                    f"\nGenerating Django model for table '{sa_model.__tablename__}'"
                )

                cls.register_table(meta.db_table, name)

                ins = sa.inspect(sa_model.__table__)

                # make foreign keys
                fks = cls.foreign_keys(sa_model)
                fk_names = set()
                for k, v in fks.items():
                    if k not in attrs:
                        attrs[k] = v
                        fk_names.add(v.db_column)

                # make many to many fields
                m2ms = cls.many_to_many_fields(sa_model)
                m2m_names = set()
                for field, v in m2ms.items():
                    class_name = f"{name}"
                    full_field = f"{class_name}.{field}"
                    if field not in attrs and full_field not in cls.related_fields:
                        attrs[field] = dm.ManyToManyField(**v)
                        m2m_names.add(field)
                        related_field = f"{v['to']}.{v['related_name']}"
                        cls.related_fields.add(related_field)

                # make columns
                for col in ins.columns:
                    if col.name in fk_names | m2m_names:
                        continue
                    if col.name not in attrs:
                        attrs[col.name] = map_column(col)

                # TODO keep track of created columns, and recreate if new sa_model is received
        return super().__new__(cls, name, bases, attrs, **kwargs)

    @classmethod
    def foreign_keys(mcs, sa_model) -> Dict[str, dm.ForeignKey]:
        inspection = sa.inspect(sa_model)
        fks = {}
        table_name = sa_model.__tablename__
        for column in inspection.columns:
            for fk in column.foreign_keys:
                target_col = fk.column

                # try to find matching relation
                relations = mcs.relations_with_column(column, inspection)
                relation = relations[0] if relations else None
                if relation:
                    field_name = relation.key
                    related_name = relation.back_populates
                    if related_name is None:
                        related_name = "+"
                    if len(relation.local_remote_pairs) > 1:
                        logger.error("Foreign key with more than one column. Skipping")
                        continue
                    pair = relation.local_remote_pairs[0]
                    if pair[1] != target_col:
                        raise ValueError("target_col in FK != target col in relation")
                else:
                    continue
                nullable = column.nullable
                to_field = target_col.name
                remote_table = target_col.table.name
                if remote_table == table_name:
                    to = "self"
                else:
                    to = mcs.table_mapping[remote_table]
                fks[field_name] = dm.ForeignKey(
                    to,
                    on_delete=dm.CASCADE,
                    db_column=column.name,
                    to_field=to_field,
                    related_name=related_name,
                    null=nullable,
                    blank=nullable,
                )
        return fks

    @classmethod
    def relations_with_column(
        mcs, column: Column, mapper: Mapper, direction: str = "MANYTOONE"
    ) -> List[RelationshipProperty]:
        """Return relationships in the mapper that use a given column on "this"
        side of the relationship.

        Parameters
        ----------
        column : sqlalchemy.Column
            foreign key to search for
        direction : {"MANYTOONE", "MANYTOMANY", "ONETOMANY"}, optional
            filter for the direction of the relationship. The default is "MANYTOONE".
        """
        relations = [
            r
            for r in mapper.relationships
            if r.direction == symbol("MANYTOONE")
            and r.local_remote_pairs[0][0] == column
        ]
        return relations

    @classmethod
    def many_to_many_fields(mcs, sa_model):
        inspection = sa.inspect(sa_model)
        table_name = sa_model.__tablename__

        m2ms = {}
        for relation in inspection.relationships:
            if relation.direction != symbol("MANYTOMANY"):
                continue
            name = relation.key
            sa_through_table = relation.secondary
            dj_through_table = mcs.table_mapping[relation.secondary.name]
            through_mapper = get_mapper(sa_through_table)
            related_name = relation.back_populates
            if len(relation.remote_side) != 2:
                raise SA2DjangoException("This is unexpected")
            tf1 = relation.synchronize_pairs[0][1]
            tf2 = relation.secondary_synchronize_pairs[0][1]
            through_fields = (
                mcs.field_name_for_fk_relation(tf1, through_mapper),
                mcs.field_name_for_fk_relation(tf2, through_mapper),
            )
            if len(relation.local_columns) > 1:
                logger.warning("Many to many with more than one columns. Ignoring.")
                continue
            remote_table = relation.mapper.local_table.name
            if remote_table == table_name:
                to = "self"
            else:
                to = mcs.table_mapping[remote_table]
            m2ms[name] = dict(
                to=to,
                through=dj_through_table,
                through_fields=through_fields,
                related_name=related_name,
            )
        return m2ms

    @classmethod
    def field_name_for_fk_relation(mcs, column: Column, mapper: Mapper) -> str:
        """ Return field name for a relation that uses a certain column """
        tf1_relations = mcs.relations_with_column(column, mapper)
        if len(tf1_relations) == 0:
            raise SA2DjangoException(
                f"no relationship using {column.name} in table {mapper.class_.__name__}"
            )
        elif len(tf1_relations) > 1:
            raise SA2DjangoException(
                f"more than one relationship using {column.name} in {mapper.class_.__name__}"
            )
        return tf1_relations[0].key


class SA2DModel(dm.Model, metaclass=SA2DBase):
    class Meta:
        abstract = True
        managed = False


def register_table(tablename: str, dm_model_name: str):
    SA2DBase.register_table(tablename, dm_model_name)


# def find_foreign_key_field_name(foreign_key: Column):


def generate_django_model(sa_model_class: type, modulename: str) -> type:
    """Generate a single django model from a single sqlalchemy declarative mapper.

    Parameters
    ----------
    sa_model_class : DeclarativeBase
        sqlalchemy model class
    modulename : str
        the __module__ attribute of the django model is set to this value

    """
    tablename = sa_model_class.__tablename__
    meta = type("Meta", (object,), {"sa_model": sa_model_class, "db_table": tablename})
    django_model = type(
        sa_model_class.__name__,
        (SA2DModel,),
        {
            "Meta": meta,
            "__module__": modulename,
        },
    )
    return django_model


def generate_sa2d_models(base, modulename: str) -> List[type]:
    """Generate django models from all declarative base models in a sqlalchemy base.

    Parameters
    ----------
    base : DeclarativeBase
        base from which to extract models
    modulename : str
        The __module__ attribute of the generated classes is set to this

    Returns
    -------
    django_models : list[type]
        list of django model classes
    """
    tables = extract_tables_from_base(base)
    # register all tables
    for tablename, sa_class in tables.items():
        register_table(tablename, sa_class.__name__)

    # generate all django models
    django_models = []
    for sa_class in tables.values():
        django_model = generate_django_model(sa_class, modulename)
        django_models.append(django_model)
    return django_models


def extract_tables_from_base(base) -> Dict[str, type]:
    """Extract tables and sqlalchemy declarative base classes from a base.

    Parameters
    ----------
    base : DeclarativeBase
        base from which to extract the model classes

    Returns
    -------
    result : dict[str, type]
        dictionary from tablename to sqlalchemy model class
    """
    tables = {}
    registry = base._decl_class_registry
    for dbase in registry.data.values():
        try:
            tablename = dbase().__table__.name
        except AttributeError:
            continue  # ignore _ModuleMarker
        else:
            modelclass = dbase().__mapper__.class_
            tables[tablename] = modelclass

    return tables


def inject_models(models: List[type], namespace: Dict[str, Any]) -> None:
    for Model in models:
        namespace[Model.__name__] = Model
