# -*- coding: utf-8 -*-
import os
from unittest import TestCase
import tempfile

from server import db


def use_temp_db(filename):
    def _use_temp_db(fn):
        def wrapper(obj):
            with tempfile.TemporaryDirectory() as dirname:
                fn(obj, os.path.join(dirname, filename))
        return wrapper
    return _use_temp_db


class TestMatchResultDBController(TestCase):
    @use_temp_db('test.db')
    def test_add_one(self, filename):
        logger = db.MatchResultDBController(filename)
        with logger as lg:
            lg.add(0, 1, 2, 0)
            lg.add(1, 2, 3, 0)

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 1,
            'winner': 2,
            'loser': 3,
            'trigger_id': 0,
        })

    @use_temp_db('test.db')
    def test_add_list(self, filename):
        logger = db.MatchResultDBController(filename)
        with logger as lg:
            lg.add((0, 1), (1, 2), (2, 3), (0, 0))

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 1,
            'winner': 2,
            'loser': 3,
            'trigger_id': 0,
        })

    @use_temp_db('test.db')
    def test_add_list2(self, filename):
        logger = db.MatchResultDBController(filename)
        with logger as lg:
            lg.add((0, 1), (1, 2), (2, 3), 0)

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 1,
            'winner': 2,
            'loser': 3,
            'trigger_id': 0,
        })

    @use_temp_db('test.db')
    def test_delete(self, filename):
        logger = db.MatchResultDBController(filename)
        with logger as lg:
            lg.add((0, 1), (1, 3), (2, 4), 0)
            lg.add((2, 3), (5, 7), (6, 8), 2)

        with logger as lg:
            lg.delete(0)

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 3,
            'winner': 7,
            'loser': 8,
            'trigger_id': 2,
        })


class TestRatedMatchResultDBController(TestCase):
    @use_temp_db('test.db')
    def test_add_one(self, filename):
        logger = db.RatedMatchResultDBController(filename)
        with logger as lg:
            lg.add(0, 1, 2, 0, 1400.0, 1600.0)
            lg.add(1, 2, 3, 0, 1550, 1450)

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 1,
            'winner': 2,
            'loser': 3,
            'trigger_id': 0,
            'winner_rate': 1550.0,
            'loser_rate': 1450.0,
        })

    @use_temp_db('test.db')
    def test_add_list(self, filename):
        logger = db.RatedMatchResultDBController(filename)
        with logger as lg:
            lg.add((0, 1), (1, 2), (2, 3), 0, (1400, 1550), (1600, 1450))

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 1,
            'winner': 2,
            'loser': 3,
            'trigger_id': 0,
            'winner_rate': 1550.0,
            'loser_rate': 1450.0,
        })

    @use_temp_db('test.db')
    def test_add_delete(self, filename):
        logger = db.RatedMatchResultDBController(filename)
        with logger as lg:
            lg.add((0, 1), (1, 2), (2, 3), 0, (1400, 1550), (1600, 1450))
            lg.add((2, 3), (5, 6), (7, 8), 2, (1300, 1700), (1510, 1490))

        with logger as lg:
            lg.delete(0)

        results = lg.get()
        self.assertTrue(len(results), 2)
        self.assertEqual(results[1], {
            'id': 3,
            'winner': 6,
            'loser': 8,
            'trigger_id': 2,
            'winner_rate': 1700.0,
            'loser_rate': 1490.0,
        })


class TestItemLabelDBController(TestCase):
    @use_temp_db('test.db')
    def test_add_one(self, filename):
        logger = db.ItemLabelDBController(filename)
        with logger as lg:
            lg.add(0, 'foo')
            lg.add(1, 'bar')

        results = lg.get()
        self.assertEqual(results, [
            {'id': 0, 'label': 'foo'},
            {'id': 1, 'label': 'bar'},
        ])

    @use_temp_db('test.db')
    def test_add_list(self, filename):
        logger = db.ItemLabelDBController(filename)
        with logger as lg:
            lg.add((0, 1), ('foo', 'bar'))

        results = lg.get()
        self.assertEqual(results, [
            {'id': 0, 'label': 'foo'},
            {'id': 1, 'label': 'bar'},
        ])

    @use_temp_db('test.db')
    def test_delete(self, filename):
        logger = db.ItemLabelDBController(filename)
        with logger as lg:
            lg.add((0, 1), ('foo', 'bar'))

        with logger as lg:
            lg.delete('foo')

        results = lg.get()
        self.assertEqual(results, [
            {'id': 1, 'label': 'bar'},
        ])
