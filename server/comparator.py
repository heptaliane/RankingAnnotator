# -*- coding: utf-8 -*-
from typing import NoReturn, Tuple, List, Any

import numpy as np
from nptyping import NDArray

from . import db
from .match_result import MatchResult


class MatchComparator():
    def __init__(self, n_items: int, logger: db.MatchResultDBController):
        self._result = np.full((n_items, n_items), MatchResult.NONE)
        self._result[range(n_items), range(n_items)] = MatchResult.DRAW
        self._trigger_id = set()
        self._current_match = 1
        self._logger = logger
        self._load_log()

    @property
    def n_match(self) -> int:
        n_result = self._result.shape[0]
        return n_result * (n_result - 1) // 2

    @property
    def n_finished(self) -> int:
        n_result = self._result.shape[0]  # Diagonal elements
        n_not_null = np.count_nonzero(self._result != MatchResult.NONE)
        return (n_not_null - n_result) // 2

    @property
    def match_result(self) -> NDArray[(Any, Any), int]:
        result = self._result.view()
        result.flags.writeable = False
        return result

    def _load_log(self) -> NoReturn:
        matches = self._logger.get(ordered=True)

        for match in matches:
            winner, loser = match.get('winner'), match.get('loser')
            self._result[winner, loser] = MatchResult.WIN
            self._result[loser, winner] = MatchResult.LOSE
            self._trigger_id.add(match.get('trigger_id'))

        if len(matches) > 0:
            self._current_match = matches[-1].get('id') + 1

    def _get_transitive_results(self, winner: int, loser: int
                                ) -> List[Tuple[int]]:
        transitive_winners = np.where(
                (self._result[winner] == MatchResult.LOSE) &
                (self._result[loser] == MatchResult.NONE)
        )
        transitive_losers = np.where(
                (self._result[winner] == MatchResult.NONE) &
                (self._result[loser] == MatchResult.WIN)
        )
        return [(twinner, loser) for twinner in transitive_winners[0]] + \
               [(winner, tloser) for tloser in transitive_losers[0]]

    def _set_match_result(self, winner: int, loser: int,
                          trigger_id: int) -> NoReturn:
        if self._result[winner, loser] != MatchResult.NONE:
            return

        self._result[winner, loser] = MatchResult.WIN
        self._result[loser, winner] = MatchResult.LOSE
        self._logger.add(match_ids=self._current_match,
                         winners=winner,
                         losers=loser,
                         trigger_ids=trigger_id)
        self._current_match += 1

    def set_match_result(self, winner: int, loser: int) -> NoReturn:
        trigger_id = self._current_match
        self._trigger_id.add(trigger_id)

        with self._logger:
            self._set_match_result(winner, loser, trigger_id)

            transitive_results = self._get_transitive_results(winner, loser)
            while len(transitive_results) > 0:
                new_transitive_results = list()
                for (twinner, tloser) in transitive_results:
                    self._set_match_result(twinner, tloser, trigger_id)
                    new_transitive_results.extend(
                            self._get_transitive_results(twinner, tloser))
                transitive_results = new_transitive_results

    def strip_match_result(self) -> NoReturn:
        strip_id = max(self._trigger_id)

        with self._logger:
            matches = self._logger.delete(strip_id)

        for match in matches:
            winner, loser = match.get('winner'), match.get('loser')
            self._result[(winner, loser), (loser, winner)] = MatchResult.NONE

        self._trigger_id.remove(strip_id)
        self._current_match = self._logger.current_id + 1


class RatedMatchComparator(MatchComparator):
    def __init__(self, n_items: int, logger: db.RatedMatchResultDBController):
        self._result = np.full((n_items, n_items), MatchResult.NONE)
        self._result[range(n_items), range(n_items)] = MatchResult.DRAW
        self._rate = np.full((n_items,), 1500, dtype=np.float32)
        self._trigger_id = set()
        self._current_match = 1
        self._logger = logger
        self._load_log()

    @property
    def rating(self) -> NDArray[(Any), float]:
        rate = self._rate.view()
        rate.flags.writeable = False
        return rate

    def _calc_victory_probability(self, rate_diff: float) -> float:
        return 1.0 / (10 ** (-rate_diff * 0.0025) + 1)

    def _update_rating(self, winner: int, loser: int) -> NoReturn:
        rate_diff = self._rate[loser] - self._rate[winner]
        wba = self._calc_victory_probability(rate_diff)
        self._rate[winner] += 32 * wba
        self._rate[loser] -= 32 * wba

    def _load_log(self) -> NoReturn:
        matches = self._logger.get(ordered=True)

        for match in matches:
            winner, loser = match.get('winner'), match.get('loser')
            self._result[winner, loser] = MatchResult.WIN
            self._result[loser, winner] = MatchResult.LOSE
            self._trigger_id.add(match.get('trigger_id'))
            self._update_rating(winner, loser)

        if len(matches) > 0:
            self._current_match = matches[-1].get('id') + 1

    def _set_match_result(self, winner: int, loser: int,
                          trigger_id: int) -> NoReturn:
        if self._result[winner, loser] != MatchResult.NONE:
            return

        self._result[winner, loser] = MatchResult.WIN
        self._result[loser, winner] = MatchResult.LOSE
        self._logger.add(match_ids=self._current_match,
                         winners=winner,
                         losers=loser,
                         trigger_ids=trigger_id,
                         winner_rates=self._rate[winner],
                         loser_rates=self._rate[loser])
        self._update_rating(winner, loser)

        self._current_match += 1

    def strip_match_result(self) -> NoReturn:
        strip_id = max(self._trigger_id)

        with self._logger:
            matches = self._logger.delete(strip_id)

        for match in matches[::-1]:
            winner, loser = match.get('winner'), match.get('loser')
            wrate, lrate = match.get('winner_rate'), match.get('loser_rate')
            self._result[(winner, loser), (loser, winner)] = MatchResult.NONE
            self._rate[winner] = wrate
            self._rate[loser] = lrate

        self._trigger_id.remove(strip_id)
        self._current_match = self._logger.current_id + 1


class PseudoRatedMatchComparator(RatedMatchComparator):
    def _calc_victory_probability(self, rate_diff: float) -> float:
        return rate_diff * 0.00125 + 0.5
