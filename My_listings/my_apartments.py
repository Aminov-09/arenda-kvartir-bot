# rent_an_apartment/my_apartments.py

from aiogram import types, Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete, update

from My_listings.delete_apartment import delete_apartment_by_index
from card_apartment.caption import format_ad_caption
from database.database import AsyncSessionLocal
# Импортируем вашу модель Table "apartment"
from Rent_out_an_apartment.db_models import apartment as ApartmentTable


router = Router()


# FSM-состояние для управления моими объявлениями
class MyApartmentsForm(StatesGroup):
    viewing_my_apartments = State()
    # Можете добавить другие состояния для редактирования (например, editing_price = State())


# Хранилище для отслеживания текущего объявления пользователя
user_ad_index = {}


@router.message(F.text == "🔍 Мои объявления")
async def show_my_apartments_start(message: types.Message, state: FSMContext, bot: Bot):
    user_id_tg = message.from_user.id
    user_ad_index[user_id_tg] = {"index": 0}
    await state.set_state(MyApartmentsForm.viewing_my_apartments)

    # Отправляем ПЕРВОЕ сообщение (message_id = None)
    await send_my_apartment_card(bot, message.chat.id, user_id_tg, state, message_id=None)


@router.callback_query(MyApartmentsForm.viewing_my_apartments, F.data.in_(['next_my_ad', 'prev_my_ad', 'delete_my_ad']))
async def navigate_my_apartments(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id_tg = callback_query.from_user.id
    user_data = user_ad_index.get(user_id_tg, {"index": 0})
    current_index = user_data["index"]

    if callback_query.data == 'delete_my_ad':
        await delete_apartment_by_index(user_id_tg, current_index)
        await bot.answer_callback_query(callback_query.id, text="Объявление удалено!")
        # Индекс остается прежним, так как удаленный элемент исчез, мы покажем следующий
    elif callback_query.data == 'next_my_ad':
        user_data["index"] = current_index + 1
    elif callback_query.data == 'prev_my_ad':
        if current_index > 0:
            user_data["index"] = current_index - 1
        else:
            await bot.answer_callback_query(callback_query.id, text="Это ваше первое объявление.")
            return

    user_ad_index[user_id_tg] = user_data

    # --- ИСПРАВЛЕНИЕ ЛОГИКИ ---
    # Мы НЕ удаляем старое сообщение и НЕ отправляем новое.
    # Мы РЕДАКТИРУЕМ текущее сообщение.
    await send_my_apartment_card(
        bot,
        callback_query.message.chat.id,
        user_id_tg,
        state,
        message_id=callback_query.message.message_id  # Передаем ID сообщения для редактирования
    )
    await bot.answer_callback_query(callback_query.id)


# Обновляем сигнатуру функции, чтобы принимать message_id
async def send_my_apartment_card(bot: Bot, chat_id: int, user_id_tg: int, state: FSMContext, message_id: int = None):
    user_data = user_ad_index.get(user_id_tg, {"index": 0})
    index = user_data["index"]
    async with AsyncSessionLocal() as session:
        query = select(ApartmentTable).where(
            ApartmentTable.c.owner == user_id_tg
        ).offset(index).limit(1)
        result = await session.execute(query)
        ad = result.first()


    if ad:
        # Используем format_ad_caption из utils/ad_templates.py
        caption = format_ad_caption(ad, index)

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ Удалить", callback_data="delete_my_ad")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_my_ad"),
                types.InlineKeyboardButton(text="➡️ Далее", callback_data="next_my_ad")
            ]
        ])

        # --- ИСПРАВЛЕНИЕ ЛОГИКИ ---
        if message_id:
            # Если message_id передан, редактируем существующее сообщение
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Иначе отправляем новое (при первом запуске)
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        msg_text = "У вас пока нет активных объявлений."
        if index > 0:
            user_ad_index[user_id_tg]["index"] = 0

            # --- ИСПРАВЛЕНИЕ ЛОГИКИ ---
        if message_id:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg_text, reply_markup=None)
        else:
            await bot.send_message(chat_id=chat_id, text=msg_text)

        await state.clear()