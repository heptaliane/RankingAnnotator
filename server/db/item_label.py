# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String

from .base import Base


class ItemLabel(Base):
    __tablename__ = 'item_label'

    id = Column(Integer, autoincrement=True, primary_key=True)
    label = Column(String)
