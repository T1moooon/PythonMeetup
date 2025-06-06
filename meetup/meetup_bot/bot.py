from django.conf import settings
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from asgiref.sync import sync_to_async
import asyncio


from .models import (
    Mailing,
    MailingReport,
    Talk,
    get_user,
    create_user,
    get_program,
    get_talk,
    create_question,
    get_current_talks,
    start_talk,
    end_talk,
    get_speaker_questions
)
from .keyboards import (
        start_keyboard,
        guest_keyboard,
        start_speaker_keyboard,
        get_talk_inline_keyboard,
        get_program_inline_keyboard,
        back_keyboard,
        start_talk_keyboard,
        end_talk_keyboard,
        get_program_keyboard_for_speaker
)

router = Router()


class QuestionStates(StatesGroup):
    waiting_for_question = State()


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
                markup = start_speaker_keyboard
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
            reply_markup=start_speaker_keyboard
        )
    await callback.answer()


def format_datetime(dt):
    return dt.strftime("%H:%M")


# Получить программу мероприятия
@router.callback_query(F.data == "event_program")
async def get_event_program(callback):
    event, talks = await get_program()

    if not event:
        await callback.message.edit_text(
            "Программа отсутствует",
            reply_markup=back_keyboard
        )
        await callback.answer()
        return

    start_date = timezone.localtime(event.start_date).strftime("%d.%m.%Y %H:%M")
    end_date = timezone.localtime(event.end_date).strftime("%d.%m.%Y %H:%M")

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
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    if user.role == 'guest':
        await callback.message.edit_text(
            'Главное меню ',
            reply_markup=guest_keyboard
        )
    if user.role == 'speaker':
        await callback.message.edit_text(
            'Главное меню ',
            reply_markup=start_speaker_keyboard
        )
    await callback.answer()


# Назад к программе
@router.callback_query(F.data == "back_to_program")
async def back_to_program(callback):
    _, talks = await get_program()
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    if user.role == 'guest':
        await callback.message.edit_text(
            "Выберите доклад:",
            reply_markup=get_program_inline_keyboard(talks)
        )
    if user.role == 'speaker':
        await callback.message.edit_text(
            "Выберите доклад:",
            reply_markup=get_program_keyboard_for_speaker(talks)
        )
    await callback.answer()


# Список докладов
@router.callback_query(F.data.startswith("talk_"))
async def talk_details(callback, state):
    talk_id = int(callback.data.split("_")[1])
    talk = await get_talk(talk_id)
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    
    if not talk:
        await callback.answer("Доклад не найден")
        return

    await state.update_data(current_talk_id=talk_id)

    start_time = timezone.localtime(talk.start_time).strftime("%H:%M")
    end_time = timezone.localtime(talk.end_time).strftime("%H:%M")

    response = (
        f"Доклад: {talk.title}\n\n"
        f"👨‍💻 Спикер: {talk.speaker.name}\n"
        f"🕒 Время: {start_time} - {end_time}\n"
    )
    if user.role == 'guest':
        await callback.message.edit_text(
            response,
            reply_markup=get_talk_inline_keyboard(talk)
        )
    if user.role == 'speaker':
        await callback.message.edit_text(
            response,
            reply_markup=back_keyboard
        )
    await callback.answer()


# Задать вопрос
@router.callback_query(F.data.startswith("ask_question_"))
async def ask_question(callback, state):
    talk_id = int(callback.data.split("_")[2])

    now = timezone.now()
    talk = await sync_to_async(Talk.objects.filter(
        pk=talk_id,
        actual_start_time__lte=now,
        actual_end_time__isnull=True
    ).first)()

    if not talk:
        await callback.message.edit_text(
            "Этот доклад не активен в данный момент. Вы можете вернуться назад",
            reply_markup=back_keyboard,
            parse_mode=None
        )
        await callback.answer()
        return
    
    await state.update_data(talk_id=talk_id)
    await state.set_state(QuestionStates.waiting_for_question)
    await callback.message.answer(
        "Пожалуйста, введите ваш вопрос спикеру:",
        reply_markup=back_keyboard,
        parse_mode=None
    )
    await callback.answer()


@router.message(QuestionStates.waiting_for_question)
async def wait_question(message, state):
    data = await state.get_data()
    talk_id = data.get('talk_id')

    try:
        talk, user, question = await create_question(
            text=message.text,
            talk_id=talk_id,
            name=message.from_user.full_name, 
            telegram_id=message.from_user.id
            )

        if not talk:
            await message.answer(
                "Доклад уже завершился, вопросы больше не принимаются.",
                parse_mode=None
            )
            await state.clear()
            return

        await message.answer(
            f"✅ Ваш вопрос отправлен\n\n"
            f"Доклад: {talk.title}\n"
            f"Вопрос: {question.text}\n"
            f"От: {user.name}\n",
            parse_mode=None,
            reply_markup=back_keyboard
        )
    except Exception as e:
        await message.answer(
            f"Ошибка при отправке вопроса: {str(e)}",
            reply_markup=back_keyboard,
            parse_mode=None
        )
    finally:
        await state.clear()


_BOT = None


async def send_mailing(mailing):
    if _BOT:
        bot = _BOT
    else:
        bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    users = await sync_to_async(lambda: list(mailing.users.all()))()
    for user in users:
        await asyncio.sleep(1)
        try:
            await bot.send_message(user.telegram_id, mailing.text)
            await sync_to_async(MailingReport.objects.create)(user=user, mailing=mailing, status="Success")
        except TelegramBadRequest as err:
            await sync_to_async(MailingReport.objects.create)(user=user, mailing=mailing, status="Fail")
            print(err)


@receiver(m2m_changed, sender=Mailing.users.through)
async def commit_mailing(sender, instance, action, **kwargs):
    if action == "post_add":
        await send_mailing(instance)
        print('Рассылка отправлена')


@router.callback_query(F.data == "start_talk")
async def handle_start_talk(callback):
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    if not user or user.role != 'speaker':
        await callback.message.edit_text("Вы не зарегистрированы как спикер.")
        await callback.answer()
        return

    now = timezone.now()
    talk = await sync_to_async(Talk.objects.filter(
        speaker=user,
        start_time__lte=now,
        end_time__gte=now
    ).first)()

    if not talk:
        await callback.message.edit_text(
            "У вас нет запланированных докладов в данный момент.",
            reply_markup=back_keyboard
        )
        await callback.answer()
        return

    await start_talk(talk.id)
    await callback.message.edit_text(
        f"Вы начали выступление: {talk.title}\n"
        f"Время начала: {timezone.localtime(now).strftime('%H:%M')}",
        reply_markup=start_talk_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "end_talk")
async def handle_end_talk(callback):
    user = await get_user(callback.from_user.id, callback.from_user.full_name)
    if not user or user.role != 'speaker':
        await callback.message.edit_text("Вы не зарегистрированы как спикер.")
        await callback.answer()
        return

    now = timezone.now()
    talk = await sync_to_async(Talk.objects.filter(
        speaker=user,
        actual_start_time__isnull=False,
        actual_end_time__isnull=True
    ).first)()

    if not talk:
        await callback.message.edit_text("У вас нет активных докладов.")
        await callback.answer()
        return

    await end_talk(talk.id)
    await callback.message.edit_text(
        f"Вы завершили выступление: {talk.title}\n"
        f"Время окончания: {timezone.localtime(now).strftime('%H:%M')}",
        reply_markup=end_talk_keyboard
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.message(F.text == "/current_speakers")
async def current_speakers_command(message):
    talks = await get_current_talks()
    if not talks:
        await message.answer("Сейчас нет активных докладов.")
        return

    response = "Сейчас проходят следующие доклады:\n\n"
    for talk in talks:
        response += (
            f"Доклад: {talk.title}\n"
            f"Спикер: {talk.speaker.name}\n"
        )
    await message.answer(response)


@router.callback_query(F.data == "speaker_questions")
async def show_speaker_questions(callback):
    user = await get_user(callback.from_user.id, callback.from_user.full_name)

    if not user or user.role != 'speaker':
        await callback.message.edit_text("Вы не зарегистрированы как спикер.")
        await callback.answer()
        return

    questions = await get_speaker_questions(user.id)
    
    if not questions:
        await callback.message.edit_text("Пока нет ни одного вопроса к вашим докладам.")
        await callback.answer()
        return

    text = "Вопросы к вашим докладам:\n\n"
    for q in questions:
        text += (
            f"<b>Доклад:</b> {q.talk.title}\n"
            f"<b>Гость:</b> {q.guest.name or 'Без имени'}\n"
            f"<b>Вопрос:</b> {q.text}\n"
            f"{timezone.localtime(q.created_at).strftime('%d.%m %H:%M')}\n\n"
        )

    await callback.message.edit_text(text[:4000], reply_markup=end_talk_keyboard)
    await callback.answer()


@router.callback_query(F.data == "donate")
async def process_donate(callback):
    await callback.message.answer_invoice(
        title="Поддержка проекта",
        description="Спасибо за интерес к мероприятию! Вы можете поддержать нас любым удобным способом 💙",
        payload="donation_payload",
        provider_token=settings.PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label="Поддержать (100₽)", amount=10000)
        ],
        start_parameter="donate",
        need_name=False,
        need_email=False,
        is_flexible=False,
    )
    await callback.message.answer(
        "Вы можете вернуться назад:", 
        reply_markup=back_keyboard
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    total = message.successful_payment.total_amount / 100
    await message.answer(
        f"✅ Спасибо за поддержку! Вы пожертвовали {total:.2f} ₽.",
        reply_markup=guest_keyboard
    )


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
