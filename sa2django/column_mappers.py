import django.db.models as dm
import sqlalchemy as sa
from citext import CIText
from django.contrib.postgres.fields import CITextField
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql.type_api import TypeEngine


class TypeMapper:
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


class BigIntMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.BigIntegerField


class FloatMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.FloatField


class StringMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.CharField

    @classmethod
    def type_kwargs(cls, type: TypeEngine):
        return dict(max_length=type.length)


class CITextMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return CITextField


class BooleanMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.BooleanField


class BinaryMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.BinaryField


class DateMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.DateField


class DateTimeMapper(TypeMapper):
    @classmethod
    def field_cls(cls, type: TypeEngine):
        return dm.DateTimeField


type_mappers = {
    sa.Integer: IntMapper,
    sa.INTEGER: IntMapper,
    sa.String: StringMapper,
    sa.CHAR: StringMapper,
    sa.Float: FloatMapper,
    sa.FLOAT: FloatMapper,
    sa.Numeric: FloatMapper,
    CIText: CITextMapper,
    sa.Boolean: BooleanMapper,
    BYTEA: BinaryMapper,
    sa.DATE: DateMapper,
    sa.Date: DateMapper,
    sa.BIGINT: BigIntMapper,
    sa.BigInteger: BigIntMapper,
    sa.DateTime: DateTimeMapper,
    sa.DATETIME: DateTimeMapper,
}


def common_kwargs(sa_col: sa.Column):
    kwargs = dict(
        primary_key=sa_col.primary_key,
        unique=sa_col.unique,
        help_text=sa_col.description,
        null=sa_col.nullable,
        blank=sa_col.nullable,
    )
    return kwargs


def map_column(sa_col: sa.Column):
    type_mapper = type_mappers[sa_col.type.__class__]
    cls = type_mapper.field_cls(sa_col.type)
    kwargs = {}
    kwargs.update(type_mapper.type_kwargs(sa_col.type))
    kwargs.update(common_kwargs(sa_col))
    return cls(**kwargs)
