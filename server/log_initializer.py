# -*- coding: utf-8 -*-
from logging import Formatter, getLogger, StreamHandler, DEBUG


datefmt = '%Y-%m-%d %H:%M:%S'
default_fmt = Formatter('[%(asctime)s.%(msecs)03d] %(levelname)s'
                        '(%(process)d) %(name)s : %(message)s',
                        datefmt=datefmt)


try:
    import sys
    from rainbow_logging_handler import RainbowLoggingHandler
    color_msecs = ('black', None, True)
    default_handler = RainbowLoggingHandler(sys.stdout,
                                            color_msecs=color_msecs,
                                            datefmt=datefmt)
    default_handler._column_color['.'] = color_msecs
    default_handler._column_color['%(msecs)03d'] = color_msecs
except Exception:
    default_handler = StreamHandler()

default_handler.setFormatter(default_fmt)
default_handler.setLevel(DEBUG)

logger = getLogger()
logger.addHandler(default_handler)
logger.setLevel(DEBUG)


def set_root_level(level):
    global logger
    logger.setLevel(level)
