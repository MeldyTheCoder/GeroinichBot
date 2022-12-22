import os
import sqlite3
from typing import Optional, Union
import functools

import config
from time_manager import TimeManager

def message(func, e):
    print("Exception", type(e).__name__, "in", func.__name__)
    print(str(e))

def handle_with(handler, *exceptions):
    try:
        handler, cleanup = handler
    except TypeError:
        cleanup = lambda f, e: None
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                e = None
                return func(*args, **kwargs)
            except exceptions or Exception as e:
                return handler(func, e)
            finally:
                cleanup(func, e)
        return wrapper
    return decorator


# Особый порядок чтения для БД
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class DatabaseObject(object):
    def __init__(self, data: dict = None, **kwargs: Union[int, str, list, float, tuple, dict]):
        self.data = data
        if kwargs:
            self.data.update(**kwargs)
        self.none_output = None

    def __getattr__(self, item):
        try:
            return self.data[str(item)]
        except:
            return self.none_output

    def __repr__(self):
        return str(self.data)

    def get_raw(self):
        return self.data

    def key(self, key: str):
        try:
            return self.data[str(key)]
        except:
            return self.none_output

class Database:
    def __init__(self, path: Union[os.PathLike, str] = 'db.sqlite'):
        path = os.path.join(config.project_root, 'db.sqlite')
        self.__db = sqlite3.connect(path)
        self.__db.row_factory = dict_factory
        self.__cursor = self.__db.cursor()
        self.tm = TimeManager()


    def __convert_list_to_object(self, list_data: list, **kwargs):
        return [DatabaseObject(data, **kwargs) for data in list_data]

    def __convert_dict_to_object(self, dict_data: dict, **kwargs):
        return DatabaseObject(dict_data, **kwargs)

    @property
    def db(self):
        return self.__db

    @property
    def cursor(self):
        return self.__cursor

    def __select_convert_args(self, dict_data: dict, **kwargs):
        args_str = []
        args = []
        if kwargs:
            dict_data.update(**kwargs)

        for key, val in dict_data.items():
            args.append(val)
            args_str.append(f'{key} = ?')

        return args_str, args

    def __insert_convert_args(self, dict_data: dict, **kwargs):
        args_str = []
        args = []
        if kwargs:
            dict_data.update(**kwargs)

        for key, val in dict_data.items():
            args.append(val)
            args_str.append(f'{key}')

        return args_str, args

    def select(self, table: str, statements: dict = None, output_keys: list = None):
        args = []
        if not output_keys:
            query = f'SELECT * FROM {table}'
        else:
            query = f'SELECT ({", ".join(output_keys)}) FROM {table}'

        if statements:
            args_str, args = self.__select_convert_args(statements)
            query += f' WHERE {" AND ".join(args_str)}'

        self.__cursor.execute(query, args)
        return self.__convert_dict_to_object(self.__cursor.fetchone())

    def select_all(self, table: str, statements: dict = None, output_keys: list = None):
        args = []
        if not output_keys:
            query = f'SELECT * FROM {table}'
        else:
            query = f'SELECT ({", ".join(output_keys)}) FROM {table}'

        if statements:
            args_str, args = self.__select_convert_args(statements)
            query += f' WHERE {" AND ".join(args_str)}'

        self.__cursor.execute(query, args)
        return self.__convert_list_to_object(self.__cursor.fetchall())

    def __merge_tuples(self, *args: Union[tuple, list]):
        tup_new = ()
        for arg in args:
            tup_new += tuple(arg)
        return tup_new

    def update(self, table: str, update_data: dict, statements: dict = None):
        query = f'UPDATE {table} ' + 'SET {}'
        if not update_data:
            return False

        args_update_str, args_update = self.__select_convert_args(update_data)
        args = args_update
        query = query.format(', '.join(args_update_str))
        if statements:
            args_states_str, args_states = self.__select_convert_args(statements)
            query += f' WHERE {" AND ".join(args_states_str)}'
            args = self.__merge_tuples(args_update, args_states)

        self.__cursor.execute(query, args)
        self.__db.commit()
        return True

    def insert(self, table: str, insert_data: dict):
        query = f'INSERT INTO {table} ' + '({}) VALUES ({})'
        if not insert_data:
            return None
        args_str, args = self.__insert_convert_args(insert_data)
        query = query.format(', '.join(args_str), ', '.join('?'*len(args_str)))
        self.__cursor.execute(query, args)
        self.__db.commit()
        return self.__cursor.lastrowid

    def delete(self, table: str, statements: dict):
        query = f'DELETE FROM {table} WHERE ' + '{}'
        if not statements:
            return False
        args_str, args = self.__select_convert_args(statements)
        query = query.format(' AND '.join(args_str))
        self.__cursor.execute(query, args)
        self.__db.commit()
        return True

    # Уроки
    def get_lessons(self, group: int = 0, **kwargs):
        lessons = self.select_all('lessons', kwargs)
        return list(filter(lambda lesson: lesson.group_num in [0, group], lessons))

    def get_lesson(self, **kwargs):
        return self.select('lessons', kwargs)
    
    def delete_lesson(self, **kwargs):
        return self.delete('lessons', kwargs)

    def add_lesson(self, **kwargs):
        return self.insert('lessons', kwargs)

    def update_lesson(self, lesson_id: int, **kwargs):
        return self.update('lessons', kwargs, {'id': lesson_id})

    def get_lessons_today(self, group: int = 0):
        weekday = self.tm.now.isoweekday()
        semester = self.tm.current_semester
        grade = self.tm.get_grade()
        all_groups = self.get_lessons(group, weekday=weekday, semester=semester, grade=grade)
        return all_groups

    # Пользователи
    def get_users(self, **kwargs):
        return self.select_all('users', kwargs)
    
    def get_user(self, **kwargs):
        return self.select('users', kwargs)
    
    def delete_user(self, **kwargs):
        return self.delete('users', kwargs)
    
    def update_user(self, user_id: int, **kwargs):
        return self.update('users', kwargs, {'id': user_id})
    
    def add_user(self, **kwargs):
        return self.insert('users', kwargs)

    def user_registered(self, **kwargs):
        data = self.select('users', kwargs)
        return bool(data)

    # Заметки
    def get_all_notes(self, **kwargs):
        return self.select_all('notes', kwargs)

    def get_active_notes(self, **kwargs):
        current_time = self.tm.timestamp
        notes = self.get_all_notes(**kwargs)
        notes = list(filter(lambda note: note.timeEnd > current_time and not(note.status), notes))
        return notes

    def get_expired_notes(self, **kwargs):
        current_time = self.tm.timestamp
        notes = self.get_all_notes(**kwargs)
        notes = list(filter(lambda note: note.timeEnd <= current_time or note.status, notes))
        return notes

    def add_note(self, **kwargs):
        return self.insert('notes', kwargs)

    def remove_note(self, **kwargs):
        return self.delete('notes', kwargs)

    def update_note(self, note_id: int, **kwargs):
        return self.update('notes', kwargs, {'id': note_id})

    def get_note(self, **kwargs):
        return self.select('notes', kwargs)
    
    
