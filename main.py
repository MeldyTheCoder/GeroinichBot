import json

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import filters
import config
import keyboards
from checkers import Checkers
from database import Database
import asyncio
import random

from time_manager import TimeManager

app = Bot(token=config.botToken, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot=app, storage=storage)
db = Database(config.db_path)
filters = filters.Filters(db)
tm = TimeManager()
kbs = keyboards.Keyboards(db, tm)
ck = Checkers(app, db)

class Notes(StatesGroup):
    text = State()
    lesson = State()
    date = State()

@dp.message_handler(filters.isPublicMessage(), commands=['help'])
async def help(message: types.Message):
    text = '''
🔞 <b>Мои команды:</b>

/random [число_1] [число_2] - <code>вывожу рандомное число</code>.
/daily - <code>пары сегодня</code>.
/vote - <code>голосование на пары</code>.
/week - <code>пары на текущей неделе</code>.
'''
    await message.reply(text)

@dp.message_handler(filters.isPublicMessage(), commands=['random'])
async def random_number(message: types.Message):
    try:
        args = message.get_args().split(' ')
        args = [int(arg) for arg in args[0:2]]
        random_int = random.randint(min(args), max(args))
        text = f'♿️ <b>Случайное число</b>: <code>{random_int}</code>'

    except ValueError:
        text = f'❤️ <b>Введи числа ебанат.</b>\n\nЯ как по-твоему должен слова считать.'

    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'

    await message.answer(text)

@dp.message_handler(filters.isPublicMessage(), commands=['notes'])
async def notes(message: types.Message):
    try:
        notes = db.get_active_notes(chat_id=message.chat.id)
        if not notes:
            text = '🕐 <b>Напоминаний пока что нет!</b>'
            return await message.reply(text)

        text = '💬 <b>Все напоминания</b>:\n\n'
        kb = kbs.notes_menu_keyboard(notes, 0)
        return await message.reply(text, reply_markup=kb)
    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.reply(text)


@dp.callback_query_handler(filters.isPublicQuery(), filters.Query('view_notes'))
async def view_notes(query: types.CallbackQuery):
    data = json.loads(query.data)
    try:
        page = data['page']
    except:
        page = 0
    try:
        notes = db.get_active_notes(chat_id=query.message.chat.id)
        if not notes:
            text = '🕐 <b>Напоминаний пока что нет!</b>'
            return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)

        text = '💬 <b>Все напоминания</b>:\n\n'
        kb = kbs.notes_menu_keyboard(notes, page)
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=kb)

    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)


@dp.callback_query_handler(filters.Query('view_note'), filters.isPublicQuery())
async def view_note(query: types.CallbackQuery):
    data = json.loads(query.data)
    try:
        note = db.get_note(id=data['id'])
        if not note:
            text = '<b>Запрашиваемая Вами заметка не найдена!</b>'
            return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)
        lesson = db.get_lesson(id=note.lesson_id)
        if not lesson:
            lesson_name = '??'
        else:
            lesson_name = lesson.name
        text = f'''
🔈 <b>Заметка</b> <code>№{note.id}</code>:
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
<i>{note.text}</i>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
♿️ <b>Пара</b>: <code>{lesson_name}</code>
🕕 <b>Действительна до</b>: <code>{tm.strftime(note.timeEnd)}</code>
'''
        kb = kbs.note_menu_keyboard(note.id)
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=kb)
    except Exception as e:
        print(str(e))
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)

@dp.message_handler(filters.isPublicMessage(), commands=['add_note'])
async def add_note(message: types.Message, state: FSMContext):
    text = '💬 <b>Введите текст напоминания</b>:'
    await Notes.text.set()
    return await message.reply(text, reply_markup=kbs.cancel_note_keyboard())

@dp.callback_query_handler(filters.Query('cancel_note'), filters.isPublicQuery(), state=Notes)
async def cancel_note(query: types.CallbackQuery):
    try:
        await dp.current_state().finish()
        await app.delete_message(query.message.chat.id, query.message.message_id)
    except:
        pass
    text = '💤 <b>Добавление заметки отменено!</b>'
    await query.message.answer(text)


@dp.callback_query_handler(filters.Query('delete_note'), filters.isPublicQuery())
async def delete_note(query: types.CallbackQuery):
    data = json.loads(query.data)
    try:
        note = db.get_note(id=data['id'])
        if not note:
            text = '📛 <b>Запрашиваемая Вами заметка не найдена!</b>'
            return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)
        delete = db.update_note(data['id'], status=1)
        text = f'✅ <b>Заметка</b> <code>№{note.id}</code> <b>успешно удалена!</b>'
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)
    except Exception as e:
        print(str(e))
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        return await app.edit_message_text(text, chat_id=query.message.chat.id, message_id=query.message.message_id)

@dp.message_handler(filters.isPublicMessage(), state=Notes.text)
async def add_note_text(message: types.Message, state: FSMContext):
    try:
        text = message.text
        await state.update_data(note_text=text)
        text = f'🔻 <b>Теперь выберите пару, по которой хотите создать заметку: </b>'
        lessons = db.get_lessons(config.graduate_group)
        kb = kbs.note_lessons_keyboard(lessons)
        #state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
        await Notes.next()
        return await message.reply(text, reply_markup=kb)
    except Exception as e:
        print(str(e))
        try:
            await state.finish()
        except:
            pass
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.answer(text)

@dp.callback_query_handler(filters.Query('lesson_note'), filters.isPublicQuery(), state=Notes.lesson)
async def choose_note_lesson(query: types.CallbackQuery, state: FSMContext):
    try:
        data = json.loads(query.data)
        lesson = db.get_lesson(id=data['id'])
        await app.delete_message(query.message.chat.id, query.message.message_id)
        if not lesson:
            lessons = db.get_lessons(config.graduate_group)
            kb = kbs.note_lessons_keyboard(lessons)
            text = '‼️ <b>Такого урока не существует!</b>\n\nВыбирай заново:'
            return await query.message.answer(text, reply_markup=kb)

        await state.update_data(note_lesson=data['id'])
        text = '''
🕓 <b>А теперь напишите дату, до которой будет действовать напоминание: </b>

👁‍🗨  Пример: <code>1/12/2022 10:30</code>
'''
        #state = dp.current_state(chat=query.message.chat.id, user=query.message.from_user.id)
        await Notes.next()
        await query.message.answer(text, reply_markup=kbs.cancel_note_keyboard())

    except:
        try:
            await state.finish()
        except:
            pass
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await query.message.answer(text)

@dp.message_handler(filters.isPublicMessage(), commands=['peer'])
async def peer(message: types.Message):
    text = f'♿️ <b>ID Чата:</b> {message.chat.id}'
    return await message.reply(text)

@dp.message_handler(filters.isPublicMessage(), state=Notes.date)
async def note_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        await dp.current_state(chat=message.chat.id, user=message.from_user.id).finish()
    except:
        pass
    try:
        date = tm.string_to_date(message.text)
        id = db.add_note(text=data['note_text'], timeEnd=date.timestamp(), lesson_id=data['note_lesson'], chat_id=message.chat.id)
        text = f'✅ <b>Заметка №{id} успешно добавлена!</b>'
        return await message.reply(text)
    except:
        try:
            await state.finish()
        except:
            pass
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.answer(text)


@dp.message_handler(filters.isPublicMessage(), commands=['week'])
async def lessons_weekly(message: types.Message):
    try:
        lessons = db.get_lessons(group=config.graduate_group)
        lessons = sorted(lessons, key=lambda key: key.id and key.weekday)
        min_weekday = min(lessons, key=lambda elem: elem.weekday).weekday
        max_weekday = max(lessons, key=lambda elem: elem.weekday).weekday
        sorted_lessons = []
        for weekday in range(min_weekday, max_weekday+1):
            elem = list(filter(lambda element: element.weekday == weekday, lessons))
            sorted_lessons.append(elem)
        text = f'♿️ <b>Все пары на этой неделе</b>:\n\n'
        for index, week_lessons in enumerate(sorted_lessons):
            text += f'🔎 <b>{tm.get_weekday_string(index+1)}</b>:\n'
            if not week_lessons:
                text += '💤 <i>Пар нет...</i>'
            else:
                lessons = [f'{week_lessons.index(lesson)+1}. {lesson.name} - <code>{lesson.room_number} каб.</code> ({lesson.time})' for lesson in week_lessons]
                text += '\n'.join(lessons)
            text += '\n\n'
        await message.answer(text)
    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.answer(text)

@dp.message_handler(filters.isPublicMessage(), commands=['vote'])
async def vote_for_lessons(message: types.Message):
    try:
        lessons = db.get_lessons_today(config.graduate_group)
        if not lessons:
            text = '💤 <b>Сегодня нет пар, дурак...</b>'
            return await message.reply(text)
        quest = '♿️ На какие пары идем?'
        options = [f'Только на "{lesson.name}"' for lesson in lessons]
        options.append('На все пары')
        options.append('Нахуй надо')
        await app.send_poll(message.chat.id, quest, options, is_anonymous=False)
    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.answer(text)

@dp.message_handler(filters.isPublicMessage(), commands=['daily'])
async def lessons_daily(message: types.Message):
    try:
        weekday = tm.now.isoweekday()
        lessons = db.get_lessons_today(2)
        if not lessons:
            text = '💤 <b>Сегодня нет пар, дурак...</b>'
            return await message.reply(text)
        lessons = sorted(lessons, key=lambda key: key.id)
        lessons = [
            f'{lessons.index(lesson) + 1}. {lesson.name} - <code>{lesson.room_number} каб.</code> ({lesson.time})'
            for lesson in lessons]
        lessons = '\n'.join(lessons)
        text = f'♿️ <b>Пары в {tm.get_weekday_string(weekday)}</b>:\n\n{lessons}'
        await message.answer(text)
    except:
        text = '📛 <b>Упс :(</b>\n\nЧто-то пошло не по плану...'
        await message.answer(text)

executor.start_polling(dp, fast=True)