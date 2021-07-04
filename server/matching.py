# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import random
from typing import NoReturn, Tuple, Any

import numpy as np
from nptyping import NDArray

from .match_result import MatchResult


class MatchingGenerator(metaclass=ABCMeta):
    def __init__(self, match_result_view: np.ndarray) -> NoReturn:
        self._match_result = match_result_view

    def _get_no_result_matches(self) -> NDArray[(2, Any), int]:
        return np.asarray(np.where(self._match_result == MatchResult.NONE))

    @abstractmethod
    def __next__(self) -> Tuple[int, int]:
        raise NotImplementedError


class RandomMatchingGenerator(MatchingGenerator):
    def __next__(self) -> Tuple[int, int]:
        matches = self._get_no_result_matches()
        if len(matches) == 0:
            raise StopIteration

        idx = random.randint(0, matches.shape[1] - 1)
        return tuple(matches[:, idx])


class FrequencyMatchingGenerator(MatchingGenerator):
    def __next__(self) -> Tuple[int, int]:
        matches = self._get_no_result_matches()
        if len(matches) == 0:
            raise StopIteration

        cnt = np.count_nonzero(self._match_result == MatchResult.NONE, axis=1)
        n_matches = cnt[matches[0]] + cnt[matches[1]]
        less_freq_matches = matches[:, n_matches == np.max(n_matches)]

        idx = random.randint(0, less_freq_matches.shape[1] - 1)
        return tuple(less_freq_matches[:, idx])


class RatingBasedMatchingGenerator(MatchingGenerator):
    def __init__(self, match_result_view: NDArray[(Any, Any), int],
                 rating_view: NDArray[(Any,), int]):
        self._match_result = match_result_view
        self._rating = rating_view

    def _calc_victory_probability(self, rate_diff: NDArray[(Any, Any), float]
                                  ) -> NDArray[(Any, Any), float]:
        return 1.0 / (10 ** (-rate_diff * 0.0025) + 1)

    def _predict_n_transitive_gain(self) -> Tuple[NDArray[int], NDArray[int]]:
        # Out _ {i, j} := np.count_nonzero(
        #       result[i] == NONE & result[j] == RESULT)
        # RESULT = (WIN, LOSE)

        n_items = len(self._rating)
        none_mask = self._match_result == MatchResult.NONE
        none_mask = none_mask.astype(np.uint32).reshape(n_items, 1, n_items)
        win_mask = self._match_result == MatchResult.WIN
        win_mask = win_mask.astype(np.uint32).reshape(n_items, n_items, 1)
        lose_mask = self._match_result == MatchResult.LOSE
        lose_mask = lose_mask.astype(np.uint32).reshape(n_items, n_items, 1)

        n_transitive_win = np.squeeze(np.dot(none_mask, win_mask))
        n_transitive_lose = np.squeeze(np.dot(none_mask, lose_mask))

        return (n_transitive_win.astype(np.int32),
                n_transitive_lose.astype(np.int32))

    def __next__(self) -> Tuple[int, int]:
        if len(self._get_no_result_matches()) == 0:
            raise StopIteration

        rate_mat = np.tile(self._rating, (len(self._rating),))
        rate_mat = rate_mat.reshape(len(self._rating), -1)
        rate_diff = rate_mat.T - rate_mat
        wba = self._calc_victory_probability(rate_diff)

        n_win, n_lose = self._predict_n_transitive_gain()
        n_gain = n_lose + (n_win - n_lose) * wba
        n_gain[self._match_result != MatchResult.NONE] = -1

        max_gain = np.max(n_gain)
        most_valuable_match = np.asarray(np.where(n_gain == max_gain))
        idx = random.randint(0, most_valuable_match.shape[1] - 1)

        return tuple(most_valuable_match[:, idx])


class PseudoRatingBasedMatchingGenerator(RatingBasedMatchingGenerator):
    def _calc_victory_probability(self, rate_diff: NDArray[(Any, Any), float]
                                  ) -> NDArray[(Any, Any), float]:
        return rate_diff * 0.00125 + 0.5


class IntroRatingBasedMatchingGenerator(RatingBasedMatchingGenerator):
    def __next__(self) -> Tuple[int, int]:
        matches = self._get_no_result_matches()
        if len(matches) == 0:
            raise StopIteration

        n_items = self._rating.shape[0]
        i, j = np.arange(0, n_items), np.arange(-1, n_items - 1)
        idxs = np.where(self._match_result[i, j] == MatchResult.NONE)[0]

        # Use neighbor items
        if len(idxs) > 0:
            idx = random.choice(idxs)
            return (i[idx], j[idx])

        # Use rating based method
        return super().__next__()
