from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Зарегистрироваться")],
        [KeyboardButton(text="Войти")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню"
)


guest_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Программа мероприятия")],
        [KeyboardButton(text="Задать вопрос")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)


speaker_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать выступление")],
        [KeyboardButton(text="Получить вопросы")],
        [KeyboardButton(text="Закончить выступление")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)
