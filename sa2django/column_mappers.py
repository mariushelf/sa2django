import django.db.models as dm
import sqlalchemy as sa
from sqlalchemy.sql.type_api import TypeEngine


class TypeMapper:
    type

    def __init__(self):
        pass

    @classmethod
    def type_kwargs(cls, type: TypeEngine):
        return {}

    @classmethod
    def field_cls(cls, type: TypeEngine):
        raise NotImplementedError


class IntMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.IntegerField


class StringMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.CharField

    @classmethod
    def type_kwargs(cls, type: TypeEngine):
        return dict(max_length=type.length)


type_mappers = {
    sa.Integer: IntMapper,
    sa.INTEGER: IntMapper,
    sa.String: StringMapper,
}


def common_kwargs(sa_col: sa.Column):
    kwargs = dict(
        primary_key=sa_col.primary_key,
        unique=sa_col.unique,
        help_text=sa_col.description,
    )
    return kwargs


def map_column(sa_col: sa.Column):
    type_mapper = type_mappers[sa_col.type.__class__]
    cls = type_mapper.field_cls(sa_col.type)
    kwargs = {}
    kwargs.update(type_mapper.type_kwargs(sa_col.type))
    kwargs.update(common_kwargs(sa_col))
    return cls(**kwargs)