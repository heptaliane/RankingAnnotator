# -*- coding: utf-8 -*-
import os
import shutil
from unittest import TestCase
import tempfile

import numpy as np

from server.db import RatedMatchResultDBController
from server.comparator import RatedMatchComparator
from server.match_result import MatchResult
from server import matching


class TestMatchingGenerator(TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        db_name = os.path.join(self.dirname, 'test.db')
        logger = RatedMatchResultDBController(db_name)
        self.items = np.random.random((20,))
        self.comparator = RatedMatchComparator(self.items.shape[0], logger)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def comparison_loop(self, generator):
        result = self.comparator.match_result

        cnt = 0
        while np.count_nonzero(result == MatchResult.NONE):
            try:
                i, j = next(generator)
            except StopIteration:
                break
            cnt += 1
            if self.items[i] > self.items[j]:
                self.comparator.set_match_result(i, j)
            else:
                self.comparator.set_match_result(j, i)

            if cnt > self.items.shape[0] * (self.items.shape[0] - 1) // 2:
                break

        return cnt

    def test_random_matching(self):
        result = self.comparator.match_result
        generator = matching.RandomMatchingGenerator(result)
        cnt = self.comparison_loop(generator)

        self.assertEqual(np.count_nonzero(result == MatchResult.NONE), 0)
        self.assertListEqual(
            list(np.count_nonzero(result == MatchResult.WIN, axis=1)),
            list(np.argsort(np.argsort(self.items)))
        )
        print('Random matching: %d' % cnt)

    def test_frequency_matching(self):
        result = self.comparator.match_result
        generator = matching.FrequencyMatchingGenerator(result)
        cnt = self.comparison_loop(generator)

        self.assertEqual(np.count_nonzero(result == MatchResult.NONE), 0)
        self.assertListEqual(
            list(np.count_nonzero(result == MatchResult.WIN, axis=1)),
            list(np.argsort(np.argsort(self.items)))
        )
        print('Frequency based matching: %d' % cnt)

    def test_rating_based_matching(self):
        result = self.comparator.match_result
        rating = self.comparator.rating
        generator = matching.RatingBasedMatchingGenerator(result, rating)
        cnt = self.comparison_loop(generator)

        self.assertEqual(np.count_nonzero(result == MatchResult.NONE), 0)
        self.assertListEqual(
            list(np.count_nonzero(result == MatchResult.WIN, axis=1)),
            list(np.argsort(np.argsort(self.items)))
        )
        print('Rating based matching: %d' % cnt)

    def test_intro_rating_matching(self):
        result = self.comparator.match_result
        rating = self.comparator.rating
        generator = matching.IntroRatingBasedMatchingGenerator(result, rating)
        cnt = self.comparison_loop(generator)

        self.assertEqual(np.count_nonzero(result == MatchResult.NONE), 0)
        self.assertListEqual(
            list(np.count_nonzero(result == MatchResult.WIN, axis=1)),
            list(np.argsort(np.argsort(self.items)))
        )
        print('Intro rating based matching: %d' % cnt)
