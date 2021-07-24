#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import glob
import argparse
from typing import List

import numpy as np

from db import ItemLabelDBController
from server import start_server
from comparator import create_comparater
from matching import create_matching_generator
from response import ImageResponseIterator

# Logging
from logging import getLogger, INFO
import log_initializer
log_initializer.set_root_level(INFO)
logger = getLogger(__name__)
logger.setLevel(INFO)


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Ranking annotate server')
    parser.add_argument('--input_dir', '--input', '-i', required=True,
                        help='Path to input image directory')
    parser.add_argument('--output', '-o', default='ranking.db',
                        help='Path to compared result output')
    parser.add_argument('--method', '-m', default='intro',
                        choices=('random', 'freq', 'rating', 'intro'),
                        help='Image pair matching method')
    parser.add_argument('--host', default='localhost',
                        help='Host name')
    parser.add_argument('--port', '-p', default=8000, type=int,
                        help='Port no')
    parser.add_argument('--pseudo', action='store_true',
                        help='Use pseudo rating')
    parser.add_argument('--max_size', '--size', '-s', default=400, type=int,
                        help='Thumbnail image size')
    return parser.parse_args(argv)


def load_filenames(db_path: str, dirname: str) -> List[str]:
    db = ItemLabelDBController(db_path)
    items = db.get(ordered=True)
    dbnames = [item.get('label') for item in items]

    names = glob.glob(os.path.join(dirname, '*.jpg'))
    names = [os.path.basename(path) for path in names]

    if len(dbnames) > 0:
        new_names = set(names) - set(dbnames)
        current_id = max([item.get('id') for item in items])
        ids = np.arange(current_id + 1, current_id + len(new_names) + 1)
        names = np.asarray(sorted(new_names)).reshape(-1)
    else:
        names = np.asarray(sorted(names)).reshape(-1)
        ids = np.arange(len(names))

    if len(names) > 0:
        with db:
            db.add(ids, names)

    items = db.get(ordered=True)
    return [os.path.join(dirname, item.get('label')) for item in items]


def main(argv):
    args = parse_arguments(argv)
    names = load_filenames(args.output, args.input_dir)

    comparator = create_comparater(len(names), args.output,
                                   args.method in ('rating', 'intro'),
                                   args.pseudo)
    matching = create_matching_generator(comparator, args.method)
    iterator = ImageResponseIterator(names, comparator, matching,
                                     args.max_size)

    start_server(args.host, args.port, iterator, comparator)


if __name__ == '__main__':
    main(sys.argv[1:])
