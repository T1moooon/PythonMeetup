from django.conf import settings
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from .models import get_user, create_user, get_program, get_talk
from .keyboards import (
        start_keyboard,
        guest_keyboard,
        speaker_keyboard,
        get_talk_inline_keyboard,
        get_program_inline_keyboard
    )

router = Router()


@router.message(F.text == "/start")
async def start_command(message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Привет, {user_name}!\n"
        "Здесь можно зарегистрироваться, узнать программу мероприятия и задать вопросы спикерам.\n\n"
        "Выберите 'Зарегистрироваться' если вы тут впервые, либо 'Войти', если уже регистрировались",
        reply_markup=start_keyboard
    )


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


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback):
    await callback.message.edit_text('Главное меню ', reply_markup=guest_keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_program")
async def back_to_program(callback):
    _, talks = await get_program()
    await callback.message.edit_text(
        "Выберите доклад:",
        reply_markup=get_program_inline_keyboard(talks)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("talk_"))
async def talk_details(callback):
    talk_id = int(callback.data.split("_")[1])
    talk = await get_talk(talk_id)
    
    if not talk:
        await callback.answer("Доклад не найден")
        return

    response = (
        f"🎤 {talk.title}\n\n"
        f"👨‍💻 Спикер: {talk.speaker.name}\n"
        f"🕒 Время: {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
        # f"📝 Описание:\n{talk.description}\n\n"
        f"❓ Хотите задать вопрос спикеру?"
    )
    await callback.message.edit_text(response, reply_markup=get_talk_inline_keyboard(talk))
    await callback.answer()


# @router.message(F.text.startswith("Доклад:"))
# async def talk_details(message):
#     talk_id = message.text.replace("Доклад: ", "").strip()
#     talk = await get_talk(int(talk_id))
#     if talk:
#         response = (
#             f"🎤 {talk.title}\n\n"
#             f"👨‍💻 Спикер: {talk.speaker.name}\n"
#             f"🕒 Время: {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
#             f"📍 Место: {talk.location}\n\n"
#             f"📝 Описание:\n{talk.description}\n\n"
#             f"❓ Хотите задать вопрос спикеру?"
#         )
#         await message.answer(response, reply_markup=talk_keyboard)
#     else:
#         await message.answer("Доклад не найден в базе данных.")


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())