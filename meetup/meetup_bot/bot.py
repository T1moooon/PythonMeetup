from django.conf import settings
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from .models import get_user, create_user, get_program, get_talk, create_question
from .keyboards import (
        start_keyboard,
        guest_keyboard,
        speaker_keyboard,
        get_talk_inline_keyboard,
        get_program_inline_keyboard
    )

router = Router()


# Функция приветствия
@router.message(F.text == "/start")
async def start_command(message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Привет, {user_name}!\n"
        "Здесь можно зарегистрироваться, узнать программу мероприятия и задать вопросы спикерам.\n\n"
        "Выберите 'Зарегистрироваться' если вы тут впервые, либо 'Войти', если уже регистрировались",
        reply_markup=start_keyboard
    )


# Регистрация
@router.callback_query(F.data == "register")
async def register_user(callback):
    try:
        user, created = await create_user(
            telegram_id=callback.from_user.id,
            name=callback.from_user.full_name,
            role="guest"
        )
        if created:
            text = "Вы зарегистрированы как гость"
            markup = guest_keyboard
        else:
            if user.role == 'speaker':
                text = 'Вы уже зарегистрированы как спикер'
                markup = speaker_keyboard
            else: 
                text = "Вы уже зарегистрированы как гость"
                markup = guest_keyboard
                
        await callback.message.edit_text(text, reply_markup=markup)
        await callback.answer()
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при регистрации: {str(e)}")
        await callback.answer()


# Войти
@router.callback_query(F.data == "login")
async def check_registration(callback):
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    if not user:
        await callback.message.edit_text(
            "Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь.",
            reply_markup=start_keyboard
        )
    elif user.role == 'guest':
        await callback.message.edit_text(
            "Вы вошли как гость",
            reply_markup=guest_keyboard
        )
    elif user.role == 'speaker':
        await callback.message.edit_text(
            "Вы вошли как спикер",
            reply_markup=speaker_keyboard
        )
    await callback.answer()


def format_datetime(dt):
    return dt.strftime("%H:%M")


# Получить программу мероприятия
@router.callback_query(F.data == "event_program")
async def get_event_program(callback):
    event, talks = await get_program()

    if not event:
        await callback.message.edit_text("Программа отсутствует")
        await callback.answer()
        return

    start_date = event.start_date.strftime("%d.%m.%Y %H:%M")
    end_date = event.end_date.strftime("%d.%m.%Y %H:%M")

    event_description = (
        f"Мероприятие: {event.title}\n"
        f"Описание: {event.description}\n"
        f"Дата начала: {start_date}\n"
        f"Дата окончания: {end_date}\n\n"
    )

    if talks:
        await callback.message.edit_text(
            event_description,
            reply_markup=get_program_inline_keyboard(talks)
        )
        await callback.answer()
    else:
        await callback.message.edit_text('Нет доступных докладов')
        await callback.answer()


# Назад в меню
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback):
    await callback.message.edit_text('Главное меню ', reply_markup=guest_keyboard)
    await callback.answer()


# Назад к программе
@router.callback_query(F.data == "back_to_program")
async def back_to_program(callback):
    _, talks = await get_program()
    await callback.message.edit_text(
        "Выберите доклад:",
        reply_markup=get_program_inline_keyboard(talks)
    )
    await callback.answer()


class QuestionState(StatesGroup):
    waiting_for_question = State()


# Список докладов
@router.callback_query(F.data.startswith("talk_"))
async def talk_details(callback, state):
    talk_id = int(callback.data.split("_")[1])
    talk = await get_talk(talk_id)
    
    if not talk:
        await callback.answer("Доклад не найден")
        return

    await state.update_data(current_talk_id=talk_id)

    response = (
        f"Доклад: {talk.title}\n\n"
        f"👨‍💻 Спикер: {talk.speaker.name}\n"
        f"🕒 Время: {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
        # f"📝 Описание:\n{talk.description}\n\n"
        f"❓ Хотите задать вопрос спикеру?"
    )
    await callback.message.edit_text(response, reply_markup=get_talk_inline_keyboard(talk))
    await callback.answer()


# Задать вопрос
@router.callback_query(F.data.startswith("ask_question_"))
async def ask_question(callback, state):
    talk_id = int(callback.data.split("_")[2])
    
    await state.update_data(talk_id=talk_id)
    await callback.message.answer("Пожалуйста, введите ваш вопрос спикеру:")
    await callback.answer()


@router.message(F.text)
async def wait_question(message, state):
    data = await state.get_data()
    talk_id = data.get('talk_id')
    user = await get_user(message.from_user.id, message.from_user.full_name)
    
    if not talk_id:
        await message.answer("Ошибка: сначала выберите доклад")
        return
    
    try:
        question = await create_question(
            text=message.text,
            talk_id=talk_id,
            name=user
        )
        
        await message.answer(
            f"Ваш вопрос отправлен:\n\n"
            f"Доклад: {question.talk.title}\n"
            f"Вопрос: {question.text}",
            reply_markup=guest_keyboard
        )
        
    except Exception as e:
        await message.answer(f"Ошибка при отправке вопроса: {str(e)}")
    finally:
        await state.clear()

    await message.answer(
        f"Ваш вопрос отправлен:\n\n"
        f"Доклад: {question.talk.title}\n"
        f"Вопрос: {question.text}",
        reply_markup=guest_keyboard
    )


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
