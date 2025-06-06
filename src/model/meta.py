from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: https://alembic.sqlalchemy.org/en/latest/naming.html
NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


DEFAULT_SCHEMA = 'public'

metadata = MetaData(naming_convention=NAMING_CONVENTION, schema=DEFAULT_SCHEMA)

# ORM - objecct related model : python <-> databse


class Base(DeclarativeBase):
    metadata = metadata
    __table_args__ = {'schema': DEFAULT_SCHEMA}
