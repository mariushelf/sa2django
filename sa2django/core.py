import inspect
import logging
from typing import Any, Dict, List, Type

import sqlalchemy as sa
from django.db import models as dm
from django.db.models.base import ModelBase
from sqlalchemy.util import symbol

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


class SA2DBase(ModelBase):
    table_mapping = {}

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

                print(f"\nGenerating Django model for table '{sa_model.__tablename__}'")

                cls.register_table(meta.db_table, name)

                ins = sa.inspect(sa_model.__table__)

                # make foreign keys
                fks = cls.foreign_keys(sa_model)
                attrs.update(fks)
                fk_names = {fk.db_column for fk in fks.values()}

                # make many to many fields
                m2ms = cls.many_to_many_fields(sa_model)
                attrs.update(m2ms)
                m2m_names = {m2m.db_column for m2m in m2ms.values()}
                print(m2ms)

                # make columns
                for col in ins.columns:
                    if col.name in fk_names | m2m_names:
                        print(f"Skipping {col.name=}")
                        continue
                    print(f"Adding column {col.name=}")
                    attrs[col.name] = map_column(col)

                # TODO keep track of created columns, and recreate if new sa_model is received
        return super().__new__(cls, name, bases, attrs, **kwargs)

    @classmethod
    def foreign_keys(mcs, sa_model) -> Dict[str, dm.ForeignKey]:
        inspection = sa.inspect(sa_model)
        fks = {}
        print("--- foreign_keys ---")
        table_name = sa_model.__tablename__
        print(f"{table_name=}")
        all_col_names = {c.name for c in inspection.columns}
        for column in inspection.columns:
            col_name = column.name
            for fk in column.foreign_keys:
                target_col = fk.column
                print(f"{col_name=}, {target_col=}")

                # try to find matching relation
                try:
                    relations = [
                        r
                        for r in inspection.relationships
                        if r.direction == symbol("MANYTOONE")
                        and r.local_remote_pairs[0][0] == column
                    ]
                except AttributeError:
                    # relations = []
                    raise
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
                    if column.name.lower().endswith("_id"):
                        field_name = column.name[:-3]
                        while field_name in all_col_names:
                            field_name += "_"
                    else:
                        field_name = f"{column.name}_fk"
                        while field_name in all_col_names:
                            field_name += "_"
                    all_col_names.add(field_name)
                    related_name = "+"
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
                )
        return fks

    @classmethod
    def many_to_many_fields(mcs, sa_model):
        print("--- many_to_many_fields ---")
        inspection = sa.inspect(sa_model)
        table_name = sa_model.__tablename__
        print(f"{table_name=}")

        m2ms = {}
        # if not hasattr(inspection, "relationships"):
        #     return m2ms
        for relation in inspection.relationships:
            if relation.direction != symbol("MANYTOMANY"):
                continue
            name = relation.key
            through_table = mcs.table_mapping[relation.secondary.name]
            related_name = relation.back_populates
            if len(relation.remote_side) != 2:
                raise Exception("This is unexpected")
            through_fields = (
                relation.synchronize_pairs[0][1].name[:-3],
                relation.secondary_synchronize_pairs[0][1].name[:-3],
            )
            if len(relation.local_columns) > 1:
                logger.warning("Many to many with more than one columns. Ignoring.")
                continue
            remote_table = relation.mapper.local_table.name
            if remote_table == table_name:
                to = "self"
            else:
                to = mcs.table_mapping[remote_table]
            print(f"Adding ManyToManyField {name=} for {table_name=}")
            m2ms[name] = dm.ManyToManyField(
                to,
                through=through_table,
                through_fields=through_fields,
                related_name=related_name,
            )
        return m2ms


class SA2DModel(dm.Model, metaclass=SA2DBase):
    class Meta:
        abstract = True
        managed = False


def register_table(tablename: str, dm_model_name: str):
    SA2DBase.register_table(tablename, dm_model_name)


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
    print(f"{tables=}")

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
