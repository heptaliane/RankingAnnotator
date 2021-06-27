# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer

from .base import Base


class MatchResult(Base):
    __tablename__ = 'match_result'

    id = Column(Integer, primary_key=True)
    winner = Column(Integer, nullable=False)
    loser = Column(Integer, nullable=False)
    triggered_by = Column(Integer, nullable=True)


MATCH_RESULT_PRIMARY_KEY = '%s.id' % MatchResult.__tablename__
