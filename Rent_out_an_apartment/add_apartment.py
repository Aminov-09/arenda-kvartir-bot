from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import insert
import re

# Общие утилиты
from common_utils import (
    Form,
    TAJIKISTAN_LOCATIONS,
    HOUSE_TYPES,
    ROOM_OPTIONS,
    RENOVATION_OPTIONS,
    create_inline_keyboard
)

# DB
from Rent_out_an_apartment.db_schemas import ApartmentCreate
from database.database import AsyncSessionLocal
from Rent_out_an_apartment.db_models import apartment as ApartmentTable

router = Router()


# -------------------- КЛАВА "ГОТОВО" --------------------
def done_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Готово", callback_data="photos_done")
    return kb.as_markup()


# -------------------- СТАРТ --------------------
@router.message(F.text == "🔑 Сдать квартиру")
async def start_add_apartment(message: types.Message, state: FSMContext):
    await state.set_state(Form.location)
    keyboard = create_inline_keyboard(TAJIKISTAN_LOCATIONS.keys(), "add_region")
    await message.reply("Выберите область:", reply_markup=keyboard)


# -------------------- ВЫБОР РЕГИОНА --------------------
@router.callback_query(Form.location, F.data.startswith("add_region_"))
async def process_region_selection_add(callback_query: types.CallbackQuery, state: FSMContext):
    region_name = callback_query.data.split("_", 2)[-1]
    await state.update_data(selected_region=region_name)
    cities = TAJIKISTAN_LOCATIONS.get(region_name, [])
    keyboard = create_inline_keyboard(cities, "add_city")

    await callback_query.message.edit_text("Выберите город/район:", reply_markup=keyboard)
    await callback_query.answer()


# -------------------- ВЫБОР ГОРОДА --------------------
@router.callback_query(Form.location, F.data.startswith("add_city_"))
async def process_city_selection_add(callback_query: types.CallbackQuery, state: FSMContext):
    city_name = callback_query.data.split("_", 2)[-1]

    await state.update_data(location=city_name)
    await state.set_state(Form.price)

    await callback_query.message.edit_text(
        f"Выбрано: **{city_name}**.\nВведите цену (например 3500):",
        parse_mode="Markdown"
    )
    await callback_query.answer()


# -------------------- ЦЕНА --------------------
@router.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price_val = int(message.text)
        if price_val <= 0:
            raise ValueError
        await state.update_data(price=price_val)
        await state.set_state(Form.description)
        await message.reply("Введите описание объявления:")
    except:
        await message.reply("Введите корректную цену (например, 3500):")


# -------------------- ОПИСАНИЕ --------------------
@router.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    if len(message.text) < 10:
        await message.reply("Описание слишком короткое.")
        return
    await state.update_data(description=message.text)

    await state.set_state(Form.type_property)
    keyboard = create_inline_keyboard(HOUSE_TYPES, "add_type")
    await message.reply("Выберите тип жилья:", reply_markup=keyboard)


# -------------------- ТИП ЖИЛЬЯ --------------------
@router.callback_query(Form.type_property, F.data.startswith("add_type_"))
async def process_type_property_callback(callback: types.CallbackQuery, state: FSMContext):
    house_type = callback.data.split("_", 2)[-1]
    await state.update_data(type_property=house_type)

    await state.set_state(Form.rooms)
    room_buttons = [r.replace("Больше 5", "6+") for r in ROOM_OPTIONS]
    keyboard = create_inline_keyboard(room_buttons, "add_rooms")

    await callback.message.edit_text("Количество комнат:", reply_markup=keyboard)
    await callback.answer()


# -------------------- КОЛ-ВО КОМНАТ --------------------
@router.callback_query(Form.rooms, F.data.startswith("add_rooms_"))
async def process_rooms_callback(callback: types.CallbackQuery, state: FSMContext):
    rooms_raw = callback.data.split("_", 2)[-1]
    rooms_val = 6 if rooms_raw == "6+" else int(rooms_raw)
    await state.update_data(rooms=rooms_val)

    await state.set_state(Form.floor_info)
    await callback.message.edit_text("Введите этаж (число):")
    await callback.answer()


# -------------------- ЭТАЖ --------------------
@router.message(Form.floor_info)
async def process_floor(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Введите номер этажа числом, например: 5")
        return

    await state.update_data(floor=int(message.text))

    await state.set_state(Form.renovation)
    keyboard = create_inline_keyboard(RENOVATION_OPTIONS, "add_renovation")
    await message.reply("Тип ремонта:", reply_markup=keyboard)


# -------------------- ТИП РЕМОНТА --------------------
@router.callback_query(Form.renovation, F.data.startswith("add_renovation_"))
async def process_renovation_callback(callback: types.CallbackQuery, state: FSMContext):
    renovation_type = callback.data.split("_", 2)[-1]
    await state.update_data(renovation=renovation_type)

    await state.set_state(Form.tel)
    await callback.message.edit_text("Введите номер телефона без кода страны (например 918123456):")
    await callback.answer()


# -------------------- ТЕЛЕФОН --------------------
@router.message(Form.tel)
async def process_tel(message: types.Message, state: FSMContext):
    tel_val = message.text.replace(' ', '').strip()

    # Только 8–9 цифр (без +992)
    if not re.fullmatch(r'\d{8,9}', tel_val):
        await message.reply("Введите номер БЕЗ кода страны (например 918123456):")
        return

    await state.update_data(tel=tel_val)
    await state.set_state(Form.photos)
    await message.reply("Отправьте 1–10 фото квартиры:", reply_markup=done_keyboard())


# -------------------- ДОБАВЛЕНИЕ ФОТО --------------------
@router.message(Form.photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id

    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 10:
        await message.reply("Лимит — 10 фото.")
        return

    photos.append(photo_id)
    await state.update_data(photos=photos)

    await message.reply(
        f"Фото добавлено ({len(photos)}/10).",
        reply_markup=done_keyboard()
    )


# -------------------- ГОТОВО (CALLBACK) --------------------
@router.callback_query(Form.photos, F.data == "photos_done")
async def complete_photos(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["owner"] = callback.from_user.id

    photos_list = data.get("photos")
    if not photos_list:
        await callback.answer("Добавьте хотя бы одно фото.", show_alert=True)
        return

    data["photos"] = ",".join(photos_list)

    try:
        new_ad_data = ApartmentCreate(**data)
    except Exception as e:
        await callback.message.answer(f"Ошибка при обработке данных: {e}")
        return

    async with AsyncSessionLocal() as session:
        stmt = insert(ApartmentTable).values(**new_ad_data.model_dump())
        await session.execute(stmt)
        await session.commit()

    await callback.message.answer("✅ Объявление успешно добавлено!")
    await state.clear()
    await callback.answer()
