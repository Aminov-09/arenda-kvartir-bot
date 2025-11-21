# rent_an_apartment/get_apartment.py

from aiogram import types, Router, Bot, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_

# Импортируем общие данные и FSMStates
from common_utils import FilterForm, TAJIKISTAN_LOCATIONS, HOUSE_TYPES, ROOM_OPTIONS, create_inline_keyboard

from UniqueView.view_service import process_unique_view
from card_apartment.caption import format_ad_caption
from database.database import AsyncSessionLocal
from Rent_out_an_apartment.db_models import apartment as ApartmentTable

router = Router()
user_state_data = {}


@router.message(F.text == "🏠 Снять квартиру")
async def start_filter_apartment(message: types.Message, state: FSMContext, bot: Bot):
    await state.set_state(FilterForm.choosing_location)
    keyboard = create_inline_keyboard(TAJIKISTAN_LOCATIONS.keys(), "select_region")
    await message.reply("Выберите область для поиска:", reply_markup=keyboard)


@router.callback_query(FilterForm.choosing_location, F.data.startswith("select_region_"))
async def process_region_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    region_name = callback_query.data.split("_", 2)[-1]
    await state.update_data(selected_region=region_name)
    cities = TAJIKISTAN_LOCATIONS.get(region_name, [])
    keyboard = create_inline_keyboard(cities, "select_city")
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(
        "Выберите город/район:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )


@router.callback_query(FilterForm.choosing_location, F.data.startswith("select_city_"))
async def process_city_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    city_name = callback_query.data.split("_", 2)[-1]
    await state.update_data(selected_city=city_name)
    await bot.answer_callback_query(callback_query.id)

    await state.set_state(FilterForm.choosing_type)
    keyboard = create_inline_keyboard(HOUSE_TYPES, "select_type")

    await bot.edit_message_text(
        "Выберите тип жилья:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )


@router.callback_query(FilterForm.choosing_type, F.data.startswith("select_type_"))
async def process_type_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    house_type = callback_query.data.split("_", 2)[-1]
    await state.update_data(selected_type=house_type)
    await bot.answer_callback_query(callback_query.id)

    await state.set_state(FilterForm.choosing_rooms)
    keyboard = create_inline_keyboard(ROOM_OPTIONS, "select_rooms")

    await bot.edit_message_text(
        "Выберите количество комнат:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )


@router.callback_query(FilterForm.choosing_rooms, F.data.startswith("select_rooms_"))
async def process_rooms_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    rooms_count_raw = callback_query.data.split("_", 2)[-1]

    if rooms_count_raw == "Больше 5":
        rooms_count = "5+"
    else:
        rooms_count = rooms_count_raw

    await state.update_data(selected_rooms=rooms_count)
    await bot.answer_callback_query(callback_query.id)

    user_id = callback_query.from_user.id
    user_filter_data = await state.get_data()
    city_name = user_filter_data.get("selected_city")
    house_type = user_filter_data.get("selected_type")

    user_state_data[user_id] = {
        "index": 0,
        "filter_location": city_name,
        "filter_type": house_type,
        "filter_rooms": rooms_count
    }

    await state.set_state(FilterForm.viewing_apartments)
    await send_apartment_card(bot, callback_query.message.chat.id, user_id)

    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )


@router.callback_query(FilterForm.viewing_apartments, F.data.in_(['next_ad', 'prev_ad']))
async def navigate_apartments(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id
    user_data = user_state_data.get(user_id, {"index": 0, "filter_location": None})
    current_index = user_data["index"]

    if callback_query.data == 'next_ad':
        user_data["index"] = current_index + 1
    elif callback_query.data == 'prev_ad':
        if current_index > 0:
            user_data["index"] = current_index - 1
        else:
            await bot.answer_callback_query(callback_query.id, text="Это первое объявление.")
            return

    user_state_data[user_id] = user_data

    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )

    await send_apartment_card(bot, callback_query.message.chat.id, user_id)
    await bot.answer_callback_query(callback_query.id)


async def send_apartment_card(bot: Bot, chat_id, user_id):
    user_data = user_state_data.get(user_id, {})
    index = user_data.get("index", 0)
    filter_location = user_data.get("filter_location")
    filter_type = user_data.get("filter_type")
    filter_rooms = user_data.get("filter_rooms")

    async with AsyncSessionLocal() as session:
        query = select(ApartmentTable)
        conditions = []

        if filter_location:
            conditions.append(ApartmentTable.c.location.ilike(f"%{filter_location}%"))

        if filter_type:
            conditions.append(ApartmentTable.c.type_property == filter_type)

        if filter_rooms:
            if filter_rooms == "5+":
                conditions.append(ApartmentTable.c.rooms >= 5)
            else:
                try:
                    num_rooms = int(filter_rooms)
                    conditions.append(ApartmentTable.c.rooms == num_rooms)
                except ValueError:
                    pass

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(index).limit(1)
        result = await session.execute(query)
        ad = result.first()

        if ad:
            await process_unique_view(session, user_id, ad.id)
            caption = format_ad_caption(ad, index)

            photos_string = ad.photos
            photos_list = photos_string.split(',') if photos_string else []

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_ad"),
                    types.InlineKeyboardButton(text="➡️ Далее", callback_data="next_ad")
                ]
            ])

            if photos_list:
                media = [
                    types.InputMediaPhoto(
                        media=file_id,
                        caption=caption if i == 0 else "",
                        parse_mode="Markdown"
                    )
                    for i, file_id in enumerate(photos_list)
                ]
                await bot.send_media_group(chat_id=chat_id, media=media)
                await bot.send_message(chat_id=chat_id, text="👇 Навигация по объявлениям 👇", reply_markup=keyboard)
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )

        else:
            if index > 0:
                user_state_data[user_id]["index"] = 0
                msg_text = f"К сожалению, по заданным критериям больше нет объявлений."
            else:
                msg_text = f"К сожалению, по заданным критериям нет ни одного объявления."

            await bot.send_message(chat_id=chat_id, text=msg_text, parse_mode="Markdown")
