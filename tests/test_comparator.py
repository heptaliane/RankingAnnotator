# -*- coding: utf-8 -*-
import os
import shutil
from unittest import TestCase
import tempfile

import numpy as np

from server import comparator
from server import db
from server.match_result import MatchResult


class TestMatchComparator(TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        db_name = os.path.join(self.dirname, 'test.db')
        self.logger = db.MatchResultDBController(db_name)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_set_result(self):
        comp = comparator.MatchComparator(5, self.logger)
        result = comp.match_result

        comp.set_match_result(1, 0)
        self.assertEqual(result[0, 1], MatchResult.LOSE)

        comp.set_match_result(2, 1)
        self.assertEqual(result[0, 2], MatchResult.LOSE)

        comp.set_match_result(4, 3)
        comp.set_match_result(3, 2)
        self.assertTrue(np.all(result[0, 1:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[1, 2:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[2, 3:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[3, 4:] == MatchResult.LOSE))

    def test_delete(self):
        comp = comparator.MatchComparator(5, self.logger)
        result = comp.match_result

        comp.set_match_result(1, 0)
        comp.set_match_result(2, 1)
        self.assertEqual(result[0, 2], MatchResult.LOSE)

        comp.strip_match_result()
        self.assertEqual(result[1, 2], MatchResult.NONE)
        self.assertEqual(result[0, 2], MatchResult.NONE)

    def test_load(self):
        with self.logger:
            self.logger.add((0, 1, 2), (1, 2, 2), (0, 1, 0), (0, 1, 1))
        comp = comparator.MatchComparator(5, self.logger)
        result = comp.match_result

        self.assertEqual(result[0, 1], MatchResult.LOSE)
        self.assertEqual(result[0, 2], MatchResult.LOSE)


class TestRatedMatchComparator(TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        db_name = os.path.join(self.dirname, 'test.db')
        self.logger = db.RatedMatchResultDBController(db_name)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_set_result(self):
        comp = comparator.RatedMatchComparator(5, self.logger)
        result = comp.match_result
        rate = comp.rating

        comp.set_match_result(1, 0)
        self.assertEqual(result[0, 1], MatchResult.LOSE)
        self.assertTrue(abs(rate[0] - 1484.0) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1484.0, rate[0]))
        self.assertTrue(abs(rate[1] - 1516.0) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1516.0, rate[1]))

        comp.set_match_result(2, 1)
        self.assertEqual(result[0, 2], MatchResult.LOSE)
        self.assertTrue(abs(rate[0] - 1469.50) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1469.5, rate[0]))
        self.assertTrue(abs(rate[1] - 1499.26) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1499.3, rate[1]))
        self.assertTrue(abs(rate[2] - 1531.23) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1531.2, rate[2]))

        comp.set_match_result(4, 3)
        comp.set_match_result(3, 2)
        self.assertTrue(np.all(result[0, 1:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[1, 2:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[2, 3:] == MatchResult.LOSE))
        self.assertTrue(np.all(result[3, 4:] == MatchResult.LOSE))

    def test_delete(self):
        comp = comparator.RatedMatchComparator(5, self.logger)
        result = comp.match_result
        rate = comp.rating

        comp.set_match_result(1, 0)
        comp.set_match_result(2, 1)
        self.assertEqual(result[0, 2], MatchResult.LOSE)
        self.assertTrue(abs(rate[0] - 1469.50) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1469.5, rate[0]))
        self.assertTrue(abs(rate[1] - 1499.26) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1499.3, rate[1]))
        self.assertTrue(abs(rate[2] - 1531.23) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1531.2, rate[2]))

        comp.strip_match_result()
        self.assertEqual(result[1, 2], MatchResult.NONE)
        self.assertEqual(result[0, 2], MatchResult.NONE)
        self.assertTrue(abs(rate[0] - 1484.0) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1484.0, rate[0]))
        self.assertTrue(abs(rate[1] - 1516.0) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1516.0, rate[1]))
        self.assertTrue(abs(rate[2] - 1500.0) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1500.0, rate[0]))

    def test_load(self):
        with self.logger:
            self.logger.add((0, 1, 2), (1, 2, 2), (0, 1, 0), (0, 1, 1),
                            1500, 1500)
        comp = comparator.RatedMatchComparator(5, self.logger)
        result = comp.match_result
        rate = comp.rating

        self.assertEqual(result[0, 1], MatchResult.LOSE)
        self.assertEqual(result[0, 2], MatchResult.LOSE)
        self.assertTrue(abs(rate[0] - 1469.50) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1469.5, rate[0]))
        self.assertTrue(abs(rate[1] - 1499.26) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1499.3, rate[1]))
        self.assertTrue(abs(rate[2] - 1531.23) < 0.02,
                        msg='expected: %.2f, actual: %.2f' % (1531.2, rate[2]))
