# -*- coding: utf-8 -*-
import os
import json
from typing import NoReturn
from tornado import web, websocket, httpserver, ioloop

from .comparator import MatchComparator
from .response import ImageResponseIterator


# Logging
from logging import getLogger, NullHandler
logger = getLogger(__name__)
logger.addHandler(NullHandler())


class MainHandler(web.httpserver):
    def get(self):
        self.render('index.html')


class WSHandler(websocket.WebSocketHandler):
    def initialize(self, iterator: ImageResponseIterator,
                   comparator: MatchComparator) -> NoReturn:
        self._iter = iterator
        self._comparator = comparator

    def open(self) -> NoReturn:
        logger.info('Connection established.')
        self.send_data()

    def send_data(self) -> NoReturn:
        try:
            res = next(self._iter)
            self.write_message(json.dumps(res))
        except StopIteration:
            logger.info('All images have compared.')
            logger.info('Quit server')
            exit()

    def undo_match(self) -> NoReturn:
        self._comparator.strip_match_result()
        self.send_data()

    def add_match_result(self, winner: int, loser: int) -> NoReturn:
        self._comparator.set_match_result(winner, loser)
        self.send_data()

    def on_message(self, msg):
        req = json.loads(msg)

        if req['action'] == 'undo':
            self.undo_match()
        elif req['action'] == 'select':
            winner = int(req['winner'])
            loser = int(req['loser'])
            self.add_match_result(winner, loser)
            logger.info('ID[%05d] > ID[%05d]', winner, loser)
        else:
            logger.error('Unknown request: %s', req['action'])


def start_server(host: str, port: int, iterator: ImageResponseIterator,
                 comparator: MatchComparator) -> NoReturn:
    app = web.Application([
        (r'/', MainHandler),
        (r'/ws', WSHandler, dict(iterator=iterator, comparator=comparator)),
    ],
        template_path=os.path.join(os.getcwd(), 'client/dist'),
        static_path=os.path.join(os.getcwd(), 'client/dist'),
    )

    logger.info('Start server on http://%s:%d/', host, port)
    server = httpserver.HTTPServer(app)
    server.listen(port, address=host)
    ioloop.IOLoop.current().start()
