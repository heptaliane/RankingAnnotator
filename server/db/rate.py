# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, ForeignKey

from .base import Base
from .match_result import MATCH_RESULT_PRIMARY_KEY


class Rate(Base):
    __tablename__ = 'rate'

    match_id = Column(ForeignKey(MATCH_RESULT_PRIMARY_KEY), primary_key=True)
    winner_rate = Column(Float, nullable=False)
    loser_rate = Column(Float, nullable=False)
