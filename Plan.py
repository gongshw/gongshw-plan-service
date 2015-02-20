#! /usr/bin/python
# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
from flask import g
from time import time
import re

__author__ = 'gongshw'


class RequestException(Exception):
    pass


def _get_db():
    _db = getattr(g, '_db', None)
    if _db is None:
        db_path = 'data/plan.db'
        _db = sqlite3.connect(db_path)

        def make_dicts(cursor, row):
            return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))

        _db.row_factory = make_dicts
        with open('data/create.sql') as f:
            create_sql = f.read()
            _db.executescript(create_sql)
        g._db = _db
    return _db


__day_seconds = 60 * 60 * 24

__time_zone_fix_seconds = + 60 * 60 * 8  # 东八区


def _timestamp(year, month):
    if month > 12:
        return _timestamp(year + 1, month - 12)
    else:
        return (datetime(year, month, 1) - datetime(1970, 1, 1)).total_seconds()


def _check_plan_attributes(plan):
    required_attributes = ['id', 'unit', 'text', 'index', 'repeat', 'sort', 'color']
    for key in required_attributes:
        if key not in plan:
            raise RequestException('plan has no attr %s' % key)
    if 'id' in plan and not _uuid_validate(plan['id']):
        raise RequestException('plan\'s id(%s) is not a uuid' % plan['id'])
    if 'unit' in plan and plan['unit'] not in ['day', 'week', 'month']:
        raise RequestException('plan\'s unit(%s) is not day|week|month' % plan['unit'])
    if 'index' in plan and type(plan['index']) is not int or plan['index'] < 0:
        raise RequestException('plan\'s index(%s) is not a positive integer' % plan['index'])
    if 'repeat' in plan and type(plan['repeat']) is not bool:
        raise RequestException('plan\'s repeat(%s) is not a bool' % plan['repeat'])
    if 'text' in plan and len(plan['text']) == 0:
        raise RequestException('plan\'s text(%s) is empty' % plan['text'])
    if 'sort' in plan and type(plan['sort']) not in [float, int]:
        raise RequestException('plan\'s sort(%s) is not a number' % plan['sort'])
    if 'color' in plan and type(plan['color']) is not str or not _valid_hex_color(plan['color']):
        raise RequestException('plan\'s sort(%s) is not a number' % plan['sort'])


def _valid_hex_color(color):
    return re.compile(r'#[0-9A-Fa-f]{6}').match(color) is not None


_uuid_hex_pattern = re.compile('[0-9a-f]{32}\Z', re.I)


def _uuid_validate(hex_uuid):
    return _uuid_hex_pattern.match(hex_uuid) is not None


def get_time_range(index, unit):
    if unit == 'day':
        time_range = __day_seconds * index, __day_seconds * (index + 1) - 1
    elif unit == 'week':
        time_range = __day_seconds * (7 * index - 3), __day_seconds * (7 * index + 4) - 1
    elif unit == 'month':
        year = 1970 + (index + 1) / 12
        month = 1 + index % 12
        time_range = _timestamp(year, month), _timestamp(year, month + 1) - 1  # FIXME
    else:
        return False
    return time_range[0] - __time_zone_fix_seconds, time_range[1] - __time_zone_fix_seconds


def time_to_index(timestamp, unit):
    timestamp += __time_zone_fix_seconds
    if unit == 'day':
        return timestamp / __day_seconds
    elif unit == 'week':
        return (timestamp + __day_seconds * 3) / (__day_seconds * 7)
    elif unit == 'month':
        date = datetime.fromtimestamp(timestamp)
        return (date.year - 1970) * 12 + date.month - 1
    else:
        return False


def _db_execute(sql, data=()):
    _get_db().execute(sql, data)
    _get_db().commit()
    pass


def _db_query(sql, data=(), one=False):
    cur = _get_db().execute(sql, data)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def add_plan(plan):
    _check_plan_attributes(plan)
    plan_exist = _db_query('SELECT * FROM plan_meta WHERE id = ?', [plan['id']])
    if plan_exist:
        raise RequestException('this plan exists')
    insert_sql = '''INSERT INTO plan_meta (id,unit,"index",repeat,"text",color,sort,add_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
    _db_execute(insert_sql,
                [plan['id'], plan['unit'], plan['index'], plan['repeat'], plan['text'], plan['color'], plan['sort'],
                 time()])
    pass


def delete_plan(plan_id):
    _db_execute('UPDATE plan_meta SET delete_at = ?  WHERE id = ?', (time(), plan_id))


def add_plan_record(plan_id, index):
    plan = _db_query('SELECT * FROM plan_meta WHERE id = ?', [plan_id])
    if not plan:
        raise RequestException('no plan %s exist' % plan_id)
    if _db_query('SELECT * FROM plan_record WHERE meta_id = ? AND "index" =?', (plan_id, index)):
        return
    _db_execute('INSERT INTO plan_record (meta_id, "index", finish_at) VALUES (?, ?, ?)', (plan_id, index, time()))


def delete_plan_record(plan_id, index):
    plan = _db_query('SELECT * FROM plan_meta WHERE id = ?', [plan_id])
    if not plan:
        raise Exception('no plan %s exist' % plan_id)
    if _db_query('SELECT * FROM plan_record WHERE meta_id = ? AND "index" =?', (plan_id, index)):
        _db_execute('DELETE FROM plan_record WHERE meta_id = ? AND "index" =?', (plan_id, index))


def get_plans(index, unit):
    timestamp = get_time_range(index, unit)[1]
    index = time_to_index(timestamp, unit)
    plans = _db_query('''
                      SELECT m.id AS id, m.repeat AS repeat, m.text AS 'text',
                        m.color AS 'color', m.sort AS sort, r.finish_at AS finish_at
                      FROM plan_meta m LEFT JOIN plan_record r ON m.id == r.meta_id
                      WHERE m.unit = ? AND m."index" <= ? AND (m.delete_at IS NULL OR m.delete_at > ?)
                      AND r."index" = ?''', (unit, index, timestamp, index))
    if plans:
        for p in plans:
            p['repeat'] = [False, True][p['repeat']]
            p['finished'] = False if p['finish_at'] is None else True
            p.pop('finish_at', None)
    return plans


def get_current_plans(unit):
    return get_plans(time_to_index(time(), unit), unit)