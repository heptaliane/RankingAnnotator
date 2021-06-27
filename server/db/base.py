# -*- coding: utf-8 -*-
from sqlalchemy.orm import registry as orm_registry
from sqlalchemy.orm.decl_api import DeclarativeMeta


class Base(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = orm_registry()
    metadata = registry.metadata
