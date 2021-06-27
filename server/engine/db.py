# -*- coding: utf-8 -*-
import enum
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Any, NoReturn

import sqlite3
import numpy as np


class SQLSchemeType(enum.Enum):
    STR = 'text'
    INT = 'integer'
    FLOAT = 'real'
    NUMBER = 'numeric'
    NONE = 'none'


class SQLScheme():
    def __init__(self, label: str, type: SQLSchemeType, not_null: bool = True,
                 unique: bool = False, default: Any = None,
                 condition: str = '') -> NoReturn:
        self.label = label
        self._type = type
        self._not_null = not_null
        self._unique = unique
        self._default = default
        self._condition = condition

    def __str__(self) -> str:
        scheme = '%s %s' % (self.label, self._type.value)

        if self._not_null:
            scheme += ' not null'
        if self._unique:
            scheme += ' unique'
        if self._default is not None:
            scheme += ' default "%s"' % str(self._default)
        if len(self._condition) > 0:
            scheme += ' check(%s)' % self._condition

        return scheme


class SimpleSQLTable():
    def __init__(self, filename: str, name: str) -> NoReturn:
        self._conn = sqlite3.connect(filename)
        self._cursor = self._conn.cursor()
        self._name = name

        # Exclude table name
        self._exclude_name = '_%s_exclude_id' % self._name

        # Exclude column name
        self._exclude_lbl = '_%s_row_id' % self._name

        # Visible view name
        self._view_name = '_visible_%s' % self._name

        # Current remove id
        self._remove_id = self._get_current_remove_id() if self.exists() else 0

        # Current revert id
        self._revert_id = self._get_current_revert_id() if self.exists() else 0

    @property
    def view_name(self) -> str:
        return self._view_name

    def _get_current_remove_id(self) -> int:
        cmd = 'select max(%s) from %s'
        self._cursor.execute(cmd % (self._exclude_lbl, self._name))
        cur_id = self._cursor.fetchone()[0]
        return 0 if cur_id is None else cur_id + 1

    def _get_current_revert_id(self) -> int:
        cmd = 'select max(%s) from %s'
        self._cursor.execute(cmd % ('revert_id', self._exclude_name))
        cur_id = self._cursor.fetchone()[0]
        return 0 if cur_id is None else cur_id + 1

    def exists(self) -> bool:
        cmd = 'select * from sqlite_master where type="table" and name="%s"'
        self._cursor.execute(cmd % self._name)
        return self._cursor.fetchall()

    def _keys(self, name: str) -> List[str]:
        self._cursor.execute('pragma table_info(%s)' % name)
        return [col[1] for col in self._cursor.fetchall()]

    def _create(self, name: str, *schemes: List[SQLScheme]) -> NoReturn:
        str_schemes = [str(scheme) for scheme in schemes]
        cmd = 'create table %s(%s)' % (name, ','.join(str_schemes))
        self._cursor.execute(cmd)

    def create(self, *schemes: List[SQLScheme]) -> NoReturn:
        if self.exists():
            return

        exclude_scheme = SQLScheme(self._exclude_lbl,
                                   SQLSchemeType.INT, unique=True)
        self._create(self._name, exclude_scheme, *schemes)

        # Create exclude table
        exclude_scheme = SQLScheme('id', SQLSchemeType.INT, unique=True)
        revert_scheme = SQLScheme('revert_id', SQLSchemeType.INT)
        self._create(self._exclude_name, exclude_scheme, revert_scheme)

        # Create view
        cmd = 'create view %s as select %s from %s ' + \
              'where %s not in(select %s from %s)'
        str_columns = ','.join([scheme.label for scheme in schemes])
        cmd = cmd % (self._view_name, str_columns, self._name,
                     self._exclude_lbl, 'id', self._exclude_name)
        self._cursor.execute(cmd)
        self.commit()

    def _push_back(self, *values: List[Any]) -> NoReturn:
        cmd = 'insert into %s values(%s)'
        values = [str(v) for v in values]
        self._cursor.execute(cmd % (self._name, ','.join(values)))

    def push_back(self, *values: List[Any]) -> NoReturn:
        self._push_back(self._remove_id, *values)
        self._remove_id += 1

    def update(self, condition: str, **values: Dict[Any]) -> NoReturn:
        cmd = 'update %s set %s where %s'
        values = ['%s = %s' % (k, v) for (k, v) in values.items()]
        self._cursor.execute(cmd % (self._name, ','.join(values), condition))

    def pop_back(self) -> NoReturn:
        cmd = 'select max(%s) from %s where %s not in(%s)'
        self._cursor.execute(cmd % (self._exclude_lbl, self._name,
                                    self._exclude_lbl, self._exclude_name))
        idx = self._cursor.fetchone()[0]
        self.remove('%s = %d' % (self._exclude_lbl, idx))

    def remove(self, condition: str) -> NoReturn:
        cmd = 'select %s from %s where %s'
        self._cursor.execute(cmd % (self._exclude_lbl, self._name, condition))

        excludes = ['(%d, %d)' % (v[0], self._revert_id)
                    for v in self._cursor.fetchall()]
        self._cursor.execute('insert into %s values%s' % (
            self._exclude_name, ','.join(excludes)))

        self._revert_id += 1

    def revert(self) -> NoReturn:
        cmd = 'delete from %s where %s = (select max(%s) from %s)'
        self._cursor.execute(cmd % (self._exclude_name, 'revert_id',
                                    'revert_id', self._exclude_name))
        self._revert_id -= 1

    def get(self) -> Dict[np.ndarray]:
        self._cursor.execute('select * from %s' % self._view_name)
        data = np.asarray(self._cursor.fetchall())
        return {k: v for k, v in zip(self._keys(self._view_name), data.T)}

    def commit(self) -> NoReturn:
        self._conn.commit()


class DatabaseWrapper(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, filename: str) -> NoReturn:
        raise NotImplementedError

    @abstractmethod
    def append(self, *args: List[Any]) -> NoReturn:
        raise NotImplementedError

    @abstractmethod
    def get(self) -> Any:
        raise NotImplementedError


class MatchResultDatabase(DatabaseWrapper):
    def __init__(self, filename: str) -> NoReturn:
        self._db = SimpleSQLTable(filename, 'match_result')
        self._db.create(
            SQLScheme('winner', SQLSchemeType.INT),
            SQLScheme('loser', SQLSchemeType.INT),
            SQLScheme('match_id', SQLSchemeType.INT)
        )

    def rollback(self) -> NoReturn:
        self._db.remove(
            'match_id = (select max(match_id) from %s)' % self._db.view_name)
        self._db.commit()

    def revert(self) -> NoReturn:
        self._db.revert()
        self._db.commit()

    def append(self, winners: List[int], losers: List[int],
               match_id: int) -> NoReturn:
        for winner, loser in zip(winners, losers):
            self._db.push_back(winner, loser, match_id)
        self._db.commit()

    def get(self) -> Dict[np.ndarray]:
        return self._db.get()


class RatedMatchResultDatabase(MatchResultDatabase):
    def __init__(self, filename: str) -> NoReturn:
        self._db = SimpleSQLTable(filename, 'match_result')
        self._db.create(
            SQLScheme('winner', SQLSchemeType.INT),
            SQLScheme('loser', SQLSchemeType.INT),
            SQLScheme('match_id', SQLSchemeType.INT),
            SQLScheme('winner_rate', SQLSchemeType.FLOAT),
            SQLScheme('loser_rate', SQLSchemeType.FLOAT)
        )

    def append(self, winners: List[int], losers: List[int], match_id: int,
               winner_rate: List[float], loser_rate: List[float]) -> NoReturn:
        for w, l, wr, lr in \
                zip(winners, losers, winner_rate, loser_rate):
            self._db.push_back(w, l, match_id, wr, lr)
        self._db.commit()


class FilenameDatabase(DatabaseWrapper):
    def __init__(self, filename: str) -> NoReturn:
        self._db = SimpleSQLTable(filename, 'filename')
        self._db.create(
            SQLScheme('id', SQLSchemeType.INT, unique=True),
            SQLScheme('filename', SQLScheme.STR, unique=True)
        )

    def append(self, ids: List[int], filenames: List[str]) -> NoReturn:
        for file_id, filename in zip(ids, filenames):
            self._db.push_back(file_id, filename)
        self._db.commit()

    def get(self) -> Dict[int, str]:
        return self._db.get()


class NullDatabase(DatabaseWrapper):
    class _NullData():
        def __getitem__(self, _='') -> list:
            return list()

    def __init__(self, _: str = '') -> NoReturn:
        pass

    def rollback(self) -> NoReturn:
        pass

    def revert(self) -> NoReturn:
        pass

    def append(self, *args: List[Any]) -> NoReturn:
        pass

    def get(self) -> _NullData:
        return self._NullData()
