# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import NoReturn, List, Dict, Any, Tuple, Union
from functools import reduce
from collections.abc import Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import numpy as np
from nptyping import NDArray

from .base import Base
from .match_result import MatchResult
from .rate import Rate
from .item_label import ItemLabel


def _dress_params(*args: List[Any], **kwargs: Dict[Any]) ->\
            Tuple[List[NDArray[Any]], Dict[NDArray[Any]]]:
    """ Padding shorter argument with None.
    """
    max_len = reduce(
                lambda x, l: max(x, len(l))
                if isinstance(l, Iterable) and not isinstance(l, str) else x,
                [*args, *kwargs.values()], 1
            )

    args = [np.asarray([*arg, *[None] * (max_len - len(arg))])
            if isinstance(arg, Iterable) and not isinstance(arg, str)
            else np.asarray([arg] * max_len)
            for arg in args]
    kwargs = {k: np.asarray([*arg, *[None] * (max_len - len(arg))])
              if isinstance(arg, Iterable) and not isinstance(arg, str)
              else np.asarray([arg] * max_len)
              for k, arg in kwargs.items()}
    return args, kwargs


class SimpleDBController(metaclass=ABCMeta):
    _BASE_URL = 'sqlite+pysqlite:///%s'

    def __init__(self, db_path: str):
        self._engine = create_engine(self._BASE_URL % db_path)
        self._session = None
        Base.metadata.create_all(self._engine)

    def __enter__(self) -> SimpleDBController:
        return self.open()

    def __exit__(self, *_) -> NoReturn:
        self.close()

    def open(self) -> SimpleDBController:
        self._session = Session(self._engine, future=True)
        return self

    def close(self) -> NoReturn:
        self._session.commit()
        self._session.close()
        self._session = None

    @abstractmethod
    def add(self, **kwargs) -> NoReturn:
        raise NotImplementedError

    def get(self) -> List[Dict[Any]]:
        with self:
            data = self._get()
        return data

    @abstractmethod
    def _get(self) -> List[Dict[Any]]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, *kwargs) -> NoReturn:
        raise NotImplementedError


class MatchResultDBController(SimpleDBController):
    def add(self, match_ids: Union[int, NDArray[int]],
            winners: Union[int, NDArray[int]],
            losers: Union[int, NDArray[int]],
            trigger_ids: Union[int, NDArray[int]]
            ) -> NoReturn:

        args, _ = _dress_params(match_ids, winners, losers, trigger_ids)

        for id, winner, loser, triggered_by in zip(*args):
            match = MatchResult(id=id.item(),
                                winner=winner.item(),
                                loser=loser.item(),
                                triggered_by=triggered_by.item())
            self._session.add(match)

    def _get(self) -> List[Dict[Any]]:
        stmt = select(MatchResult)
        result = self._session.execute(stmt).scalars().all()
        return [
            {
                'id': row.id,
                'winner': row.winner,
                'loser': row.loser,
                'trigger_id': row.triggered_by,
            }
            for row in result
        ]

    def delete(self, triger_id: int) -> NoReturn:
        stmt = select(MatchResult).filter_by(triggered_by=triger_id)
        matches = self._session.execute(stmt).scalars().all()

        for match in matches:
            self._session.delete(match)


class RatedMatchResultDBController(SimpleDBController):
    def add(self, match_ids: Union[int, NDArray[int]],
            winners: Union[int, NDArray[int]],
            losers: Union[int, NDArray[int]],
            trigger_ids: Union[int, NDArray[int]],
            winner_rates: Union[float, NDArray[float]],
            loser_rates: Union[float, NDArray[float]]) -> NoReturn:
        args, _ = _dress_params(match_ids, winners, losers, trigger_ids,
                                winner_rates, loser_rates)

        for id, winner, loser, trigger, win_rate, lose_rate in zip(*args):
            match = MatchResult(id=id.item(),
                                winner=winner.item(),
                                loser=loser.item(),
                                triggered_by=trigger.item())
            rate = Rate(match_id=id.item(),
                        winner_rate=win_rate.item(),
                        loser_rate=lose_rate.item())
            self._session.add(match)
            self._session.add(rate)

    def _get(self) -> List[Dict[Any]]:
        stmt = select(MatchResult, Rate).\
                join(Rate, MatchResult.id == Rate.match_id)
        result = self._session.execute(stmt).all()
        return [
            {
                'id': match.id,
                'winner': match.winner,
                'loser': match.loser,
                'trigger_id': match.triggered_by,
                'winner_rate': rate.winner_rate,
                'loser_rate': rate.loser_rate,
            }
            for (match, rate) in result
        ]

    def delete(self, trigger_id: int) -> NoReturn:
        stmt = select(MatchResult, Rate).\
            filter_by(triggered_by=trigger_id).\
            join(Rate, MatchResult.id == Rate.match_id)

        result = self._session.execute(stmt)

        for (match, rate) in result:
            self._session.delete(match)
            self._session.delete(rate)


class ItemLabelDBController(SimpleDBController):
    def add(self, item_ids: Union[int, NDArray[int]],
            labels: Union[str, NDArray[str]]) -> NoReturn:
        args, _ = _dress_params(item_ids, labels)

        for id, label in zip(*args):
            item = ItemLabel(id=id.item(), label=label.item())
            self._session.add(item)

    def _get(self) -> List[Dict[Any]]:
        stmt = select(ItemLabel)
        items = self._session.execute(stmt).scalars().all()
        return [
            {
                'id': item.id,
                'label': item.label,
            }
            for item in items
        ]

    def delete(self, label: str) -> NoReturn:
        stmt = select(ItemLabel).filter_by(label=label)
        items = self._session.execute(stmt).scalars().all()

        for item in items:
            self._session.delete(item)
