from django.conf import settings
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .keyboards import start_keyboard, guest_keyboard, speaker_keyboard
from .models import get_user, create_user, get_program
import html

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


@router.message(F.text == "Зарегистрироваться")
async def register_user(message):
    try:
        user, created = await create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            role="guest"
        )
        if created:
            await message.answer("Вы зарегистрированы как гость", reply_markup=guest_keyboard)
        else:
            if user.role == 'speaker':
                await message.answer('Вы уже зарегистрированы как спикер', reply_markup=speaker_keyboard)
            else: 
                await message.answer("Вы уже зарегистрированы как гость", reply_markup=guest_keyboard)
    except Exception as e:
        await message.answer(f"Ошибка при регистрации: {str(e)}")


@router.message(F.text == "Войти")
async def check_registration(message):
    user = await get_user(message.from_user.id, message.from_user.full_name)
    if user and user.role == 'guest':
        await message.answer("Вы вошли как гость", reply_markup=guest_keyboard)
    elif user.role == 'speaker':
        await message.answer("Вы вошли как спикер", reply_markup=speaker_keyboard)
    else:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь.")


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())