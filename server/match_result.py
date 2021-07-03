# -*- coding: utf-8 -*-
from enum import IntEnum, auto


class MatchResult(IntEnum):
    NONE = auto()
    WIN = auto()
    LOSE = auto()
    DRAW = auto()
