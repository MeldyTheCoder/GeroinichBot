from aiogram import types
import json
from database import DatabaseObject, Database
from time_manager import TimeManager


class Keyboards:
    def __init__(self, db: Database, tm: TimeManager):
        self.db = db
        self.tm = TimeManager()
        self.page_elems = 10

    def note_lessons_keyboard(self, lessons: list[DatabaseObject]):
        kb = types.InlineKeyboardMarkup(1)
        for lesson in lessons:
            kb.add(types.InlineKeyboardButton(f'🔹 {lesson.name}', callback_data=json.dumps({'action': 'lesson_note', 'id': lesson.id})))
        kb.add(types.InlineKeyboardButton('↪️Отмена', callback_data=json.dumps({'action': 'cancel_note'})))
        return kb

    def __page_system(self, callback: str, list: list, page: int = 0, **kwargs):
        buttons = []
        list_cut = list[(page*self.page_elems):((page+1)*self.page_elems)]
        if page > 0:
            callback_data = {'action': callback, 'page': page-1}
            if kwargs:
                callback_data.update(**kwargs)
            buttons.append(types.InlineKeyboardButton(f'⬅️ {page}', callback_data=json.dumps(callback_data)))
        if len(list) > len(list_cut)*(page+1):
            callback_data = {'action' : callback, 'page' : page + 1}
            if kwargs :
                callback_data.update(**kwargs)
            buttons.append(types.InlineKeyboardButton(f'⬅️ {page+2}', callback_data=json.dumps(callback_data)))

        return list_cut, buttons

    def cancel_note_keyboard(self):
        kb = types.InlineKeyboardMarkup(1)
        kb.add(types.InlineKeyboardButton('↪️Отмена', callback_data=json.dumps({'action': 'cancel_note'})))
        return kb

    def notes_menu_keyboard(self, notes: list, page: int = 0):
        kb = types.InlineKeyboardMarkup(2)
        notes, buttons = self.__page_system('view_notes', notes, page)
        for note in notes:
            lesson = self.db.get_lesson(id=note.lesson_id)
            kb.add(types.InlineKeyboardButton(f'{lesson.name} до {self.tm.strftime(note.timeEnd)}', callback_data=json.dumps({'action': 'view_note', 'id': note.id})))
        kb.add(*buttons)
        return kb

    def note_menu_keyboard(self, note_id: int):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🗑 Удалить', callback_data=json.dumps({'action': 'delete_note', 'id': note_id})))
        kb.add(types.InlineKeyboardButton('↪️ Назад', callback_data=json.dumps({'action': 'view_notes', 'page': 0})))
        return kb
