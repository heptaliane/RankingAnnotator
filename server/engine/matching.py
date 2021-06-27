# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import random
from typing import NoReturn, Tuple
import numpy as np

from .comparator import MatchResult


class MatchingGenerator(metaclass=ABCMeta):
    def __init__(self, match_result_view: np.ndarray) -> NoReturn:
        self._match_result = match_result_view

    def _get_no_result_matches(self) -> np.ndarray:
        return np.asarray(np.where(self._match_result == MatchResult.NONE))

    @abstractmethod
    def __call__(self):
        raise NotImplementedError


class RandomMatchingGenerator(MatchingGenerator):
    def _random_choice(self, matches: np.ndarray) -> np.ndarray:
        idx = random.randint(0, matches.shape[1])
        return matches[:, idx]

    def __call__(self) -> Tuple[int, int]:
        no_result = self._get_no_result_matches()
        return tuple(self._random_choice(no_result))


class FrequencyMatchingGenerator(RandomMatchingGenerator):
    def __call__(self) -> Tuple[int, int]:
        no_result = self._get_no_result_matches()
        cnt = np.count_nonzero(self._match_result == MatchResult.NONE, axis=1)
        n_matches = cnt[no_result[0]] + cnt[no_result[1]]

        less_freq_matches = no_result[n_matches == np.min(n_matches)]
        return tuple(self._random_choice(less_freq_matches))


class RatingBasedMatchingGenerator(MatchingGenerator):
    def __init__(self, match_result_view: np.ndarray,
                 rating_view: np.ndarray) -> NoReturn:
        self._match_result = match_result_view
        self._rating = rating_view

    def _calc_victory_probability(self, rate_diff: np.ndarray) -> np.ndarray:
        return 1.0 / (10 ** (-rate_diff / 400) + 1)

    def _predict_n_transitive_gain(self) -> Tuple[np.ndarray, np.ndarray]:
        # Out _ {i, j} := np.count_nonzero(result[i] == NONE &
        #                 result[j] == RESULT)
        # RESULT in (WIN, LOSE)

        n_items = len(self._rating)
        none_mask = self._match_result == MatchResult.NONE
        none_mask = none_mask.astype(np.uint32).reshape(n_items, 1, n_items)
        win_mask = self._match_result == MatchResult.WIN
        win_mask = win_mask.astype(np.uint32).reshape(n_items, n_items, 1)
        lose_mask = self._match_result == MatchResult.LOSE
        lose_mask = lose_mask.astype(np.uint32).reshape(n_items, n_items, 1)

        n_transitive_win = np.squeeze(np.dot(none_mask, win_mask))
        n_transitive_lose = np.squeeze(np.dot(none_mask, lose_mask))

        return (n_transitive_win, n_transitive_lose)

    def __call__(self) -> Tuple[int, int]:
        rate_mat = np.tile(self._rating, (len(self._rating),))
        rate_diff = rate_mat - rate_mat.T

        wba = self._calc_victory_probability(rate_diff)
        n_win, n_lose = self._predict_n_transitive_gain()
        n_gain = n_lose + (n_win - n_lose) * wba

        n_gain[self._match_result == MatchResult.NONE] = 0
        idx = np.argmax(n_gain)

        return (idx // len(self._rating), idx % len(self._rating))


class PseudoRatingBasedMatchingGenerator(RatingBasedMatchingGenerator):
    def _calc_victory_probability(self, rate_diff: np.ndarray) -> np.ndarray:
        return rate_diff / 800 + 0.5
