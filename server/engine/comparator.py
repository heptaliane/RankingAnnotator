# -*- coding: utf-8 -*-
from enum import IntEnum, auto
from typing import List, NoReturn

import numpy as np

from . import DatabaseWrapper, NullDatabase


class MatchResult(IntEnum):
    NONE = auto()
    WIN = auto()
    LOSE = auto()
    DRAW = auto()


class MatchComparator():
    def __init__(self, n_items: int,
                 logger: DatabaseWrapper = NullDatabase()) -> NoReturn:
        self._result = np.full((n_items, n_items), MatchResult.NONE)
        self._result[range(n_items), range(n_items)] = MatchResult.DRAW
        self._match_id = np.zeros_like(self._result, dtype=np.uint32)
        self._current_match = 0
        self._logger = logger

    @property
    def n_match(self) -> int:
        return len(self._result) * (len(self._result) - 1) // 2

    @property
    def n_finished(self) -> int:
        return (np.count_nonzero(self._match_id) - len(self._result)) // 2

    @property
    def match_result(self) -> np.ndarray:
        result = self._result.view
        result.flags.writeable = False
        return result

    def _push_log(self, winners: List[int], losers: List[int]) -> NoReturn:
        self._logger.append(winners, losers, self._current_match)

    def _set_match_result(self, winner_id: int, loser_id: int) -> NoReturn:
        if self._result[winner_id, loser_id] != MatchResult.NONE:
            return

        self._result[winner_id, loser_id] = MatchResult.WIN
        self._result[loser_id, winner_id] = MatchResult.LOSE
        self._match_id[winner_id, loser_id] = self._current_match
        self._match_id[loser_id, winner_id] = self._current_match

    def set_match_result(self, winner_id: int, loser_id: int) -> NoReturn:
        self._current_match += 1
        self._set_match_result(winner_id, loser_id)

        transitive_winners = np.where(
            self._result[winner_id] == MatchResult.LOSE)
        for transitive_winner_id in transitive_winners:
            self._set_match_result(transitive_winner_id, loser_id)

        transitive_losers = np.where(
            self._result[loser_id] == MatchResult.WIN)
        for transitive_loser_id in transitive_losers:
            self._set_match_result(loser_id, transitive_loser_id)

        self._push_log([
            winner_id,
            *transitive_winners,
            *[winner_id] * len(transitive_losers)
        ], [
            loser_id,
            *[loser_id] * len(transitive_winners),
            *transitive_losers
        ])


class RatedMatchComparator(MatchComparator):
    def __init__(self, n_items: int,
                 logger: DatabaseWrapper = NullDatabase()) -> NoReturn:
        super().__init__(n_items)
        self._rate = np.full(n_items, 1500, dtype=np.float32)

    def _push_log(self, winners: int, losers: int) -> NoReturn:
        self._logger.append(winners, losers, self._current_match,
                            self._rate[winners], self._rate[losers])

    def _calc_victory_probability(self, rate_diff: float) -> float:
        return 1.0 / (10 ** (-rate_diff / 400) + 1)

    def _update_rate(self, winner_id: int, loser_id: int) -> NoReturn:
        rate_diff = self._rate[loser_id] - self._rate[winner_id]
        wba = self._calc_victory_probability(rate_diff)
        self._rate[winner_id] += 32 * wba
        self._rate[loser_id] += 32 * wba

    def _set_match_result(self, winner_id: int, loser_id: int):
        if self._result[winner_id, loser_id] != MatchResult.NONE:
            return

        self._result[winner_id, loser_id] = MatchResult.WIN
        self._result[loser_id, winner_id] = MatchResult.LOSE
        self._match_id[winner_id, loser_id] = self._current_match
        self._match_id[loser_id, winner_id] = self._current_match

        self._update_rate(winner_id, loser_id)


class PseudoRatedMatchComparator(RatedMatchComparator):
    def _calc_victory_probability(self, rate_diff: float) -> float:
        return rate_diff / 400 + 0.5
