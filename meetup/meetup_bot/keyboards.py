from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")],
        [InlineKeyboardButton(text="Войти", callback_data="login")]
    ]
)


guest_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Программа мероприятия", callback_data="event_program")]
    ]
)


start_speaker_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Начать выступление", callback_data="start_talk")],
        [InlineKeyboardButton(text="Программа мероприятия", callback_data="event_program")]
    ]
)


start_talk_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Получить вопросы", callback_data="get_questions")]
    ]
)


end_talk_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Закончить выступление", callback_data="end_talk")]
    ]
)


def get_talk_inline_keyboard(talk):
    talk_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✍ Задать вопрос",
            callback_data=f"ask_question_{talk.pk}"
        )],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
    ])
    return talk_keyboard


def get_program_inline_keyboard(talks):
    program_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(
                    text=f"Доклад: {talk.title} {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}",
                    callback_data=f"talk_{talk.pk}"
                )] 
                for talk in talks
            ],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
        ]
    )
    return program_keyboard


def get_program_keyboard_for_speaker(talks):
    program_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(
                    text=f"Доклад: {talk.title} {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}",
                    callback_data=f"talk_{talk.pk}"
                )] 
                for talk in talks
            ],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_speaker_menu")]
        ]
    )
    return program_keyboard


back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
    ]
)
