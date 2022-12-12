import asyncio

from aiogram import types, Bot

import config
from database import Database

class Checkers:
    def __init__(self, app: Bot, db: Database):
        self.loop = asyncio.get_event_loop()
        self.app = app
        self.db = db
        self.note_check_obj = asyncio.run_coroutine_threadsafe(self.notes_checker(), self.loop)

    async def notes_checker(self):
        try:
            while True:
                notes = self.db.get_active_notes()
                chat_ids = list(set([note.chat_id for note in notes]))
                if not all(chat_ids):
                    await asyncio.sleep(config.note_checker_cooldown)
                    continue
                for chat_id in chat_ids:
                    try:
                        text = '💬 <b>Не забывайте про Ваши заметки:</b>\n\n'
                        note_elem = list(filter(lambda note: note.chat_id == chat_id, notes))
                        notes_str = [f'{index+1}. <b>{self.db.get_lesson(id=note.lesson_id).name}</b> - <code>{note.text}</code>' for index, note in enumerate(note_elem)]
                        text += '\n'.join(notes_str)
                        await self.app.send_message(chat_id, text)
                    except Exception as e:
                        print(e)

                await asyncio.sleep(config.note_checker_cooldown)
        except Exception as e:
            print('[!] NOTES CHECKER ERROR:', str(e))
