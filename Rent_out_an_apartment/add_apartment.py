# add_apartment.py

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert
import re

# Импортируем общие данные и утилиты
from common_utils import (
    Form,
    TAJIKISTAN_LOCATIONS,  # Теперь используется и здесь
    HOUSE_TYPES,
    ROOM_OPTIONS,
    RENOVATION_OPTIONS,
    create_inline_keyboard
)

# Предполагается, что эти импорты ведут к вашим файлам
from Rent_out_an_apartment.db_schemas import ApartmentCreate
from database.database import AsyncSessionLocal
from Rent_out_an_apartment.db_models import apartment as ApartmentTable

router = Router()


@router.message(F.text == "🔑 Сдать квартиру")
async def start_add_apartment(message: types.Message, state: FSMContext):
    # Вместо ввода текста сразу предлагаем выбрать регион через кнопки
    await state.set_state(Form.location)  # Используем Form.location как начальный этап выбора локации
    keyboard = create_inline_keyboard(TAJIKISTAN_LOCATIONS.keys(), "add_region")
    await message.reply("Выберите область для размещения объявления:", reply_markup=keyboard)


# Обработчик выбора РЕГИОНА
@router.callback_query(Form.location, F.data.startswith("add_region_"))
async def process_region_selection_add(callback_query: types.CallbackQuery, state: FSMContext):
    region_name = callback_query.data.split("_", 2)[-1]
    await state.update_data(selected_region=region_name)
    cities = TAJIKISTAN_LOCATIONS.get(region_name, [])
    keyboard = create_inline_keyboard(cities, "add_city")

    await callback_query.message.edit_text(
        "Выберите город/район:",
        reply_markup=keyboard
    )
    await callback_query.answer()


# Обработчик выбора ГОРОДА/РАЙОНА
@router.callback_query(Form.location, F.data.startswith("add_city_"))
async def process_city_selection_add(callback_query: types.CallbackQuery, state: FSMContext):
    city_name = callback_query.data.split("_", 2)[-1]

    # Сохраняем выбранный город в поле location FSM
    await state.update_data(location=city_name)

    # Переходим к следующему шагу: ввод цены (текстом)
    await state.set_state(Form.price)

    await callback_query.message.edit_text(
        f"Выбрано местоположение: **{city_name}**.\n\nВведите цену аренды (только число, например, 3500):",
        reply_markup=None,
        parse_mode="Markdown"
    )
    await callback_query.answer()


@router.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price_val = int(message.text)
        if price_val <= 0:
            raise ValueError("Цена должна быть положительным числом.")
        await state.update_data(price=price_val)
        await state.set_state(Form.description)
        await message.reply("Введите описание объявления (подробности, удобства):")
    except ValueError as e:
        await message.reply(f"Некорректный ввод. {e}\nВведите цену числом, например, 3500:")


@router.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    if len(message.text) < 10:
        await message.reply("Описание слишком короткое. Пожалуйста, добавьте деталей.")
        return
    await state.update_data(description=message.text)

    # Переходим к выбору типа жилья через кнопки
    await state.set_state(Form.type_property)
    keyboard = create_inline_keyboard(HOUSE_TYPES, "add_type")
    await message.reply("Выберите тип жилья:", reply_markup=keyboard)


# Обработчик callback'a для выбора типа жилья (остается без изменений)
@router.callback_query(Form.type_property, F.data.startswith("add_type_"))
async def process_type_property_callback(callback: types.CallbackQuery, state: FSMContext):
    house_type = callback.data.split("_", 2)[-1]
    await state.update_data(type_property=house_type)

    await state.set_state(Form.rooms)
    room_buttons = [r.replace("Больше 5", "6+") for r in ROOM_OPTIONS]
    keyboard = create_inline_keyboard(room_buttons, "add_rooms")

    await callback.message.edit_text("Выберите количество комнат:", reply_markup=keyboard)
    await callback.answer()


# Обработчик callback'a для выбора количества комнат (остается без изменений)
@router.callback_query(Form.rooms, F.data.startswith("add_rooms_"))
async def process_rooms_callback(callback: types.CallbackQuery, state: FSMContext):
    rooms_raw = callback.data.split("_", 2)[-1]
    rooms_val = 6 if rooms_raw == "6+" else int(rooms_raw)
    await state.update_data(rooms=rooms_val)

    await state.set_state(Form.floor_info)
    await callback.message.edit_text("Введите этаж и общее количество этажей (например, 5 из 10):", reply_markup=None)
    await callback.answer()


@router.message(Form.floor_info)
async def process_floor(message: types.Message, state: FSMContext):
    match = re.match(r'^(\d+)\s*(?:из\s*(\d+))?$', message.text, re.IGNORECASE)

    if match:
        try:
            floor_number_str = match.group(1)
            floor_number = int(floor_number_str)

            await state.update_data(floor=floor_number)

            await state.set_state(Form.renovation)
            keyboard = create_inline_keyboard(RENOVATION_OPTIONS, "add_renovation")
            await message.reply("Выберите тип ремонта:", reply_markup=keyboard)

        except ValueError:
            await message.reply("Произошла внутренняя ошибка при обработке этажа. Попробуйте ввести еще раз.")
    else:
        await message.reply("Некорректный формат. Пожалуйста, введите номер этажа (например, 5 или 5 из 10):")


@router.callback_query(Form.renovation, F.data.startswith("add_renovation_"))
# Все последующие функции (process_renovation_callback, process_tel, process_photos, complete_photos)
# остаются без изменений, так как они уже были реализованы с использованием кнопок или
# текстового ввода с валидацией, как вы просили ранее.
# ... [КОД НИЖЕ ОСТАЕТСЯ ИДЕНТИЧНЫМ ПРЕДЫДУЩЕЙ ВЕРСИИ] ...

async def process_renovation_callback(callback: types.CallbackQuery, state: FSMContext):
    renovation_type = callback.data.split("_", 2)[-1]
    await state.update_data(renovation=renovation_type)

    await state.set_state(Form.tel)
    await callback.message.edit_text("Введите номер телефона (например, +992 XXX XX XX):", reply_markup=None)
    await callback.answer()


@router.message(Form.tel)
async def process_tel(message: types.Message, state: FSMContext):
    tel_val = message.text.replace('+', '').replace(' ', '').strip()
    if not re.fullmatch(r'\d{9,15}', tel_val):
        await message.reply("Неверный формат номера. Пожалуйста, введите корректный номер.")
        return
    await state.update_data(tel=tel_val)
    await state.set_state(Form.photos)
    await message.reply("Отправьте 1–10 фото квартиры.\nКогда закончите — отправьте текст **Готово**.")


@router.message(Form.photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 10:
        await message.reply("Вы достигли лимита в 10 фотографий. Нажмите **Готово**.")
        return
    photos.append(photo_id)
    await state.update_data(photos=photos)
    await message.reply(f"Фото добавлено ({len(photos)}/10).")


@router.message(Form.photos, F.text.lower() == "готово")
async def complete_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["owner"] = message.from_user.id
    photos_list = data.get("photos")
    if not photos_list:
        await message.reply("Пожалуйста, загрузите хотя бы одно фото.")
        return
    data["photos"] = ",".join(photos_list)

    try:
        new_ad_data = ApartmentCreate(**data)
    except Exception as e:
        await message.reply(f"Произошла ошибка при подготовке данных. Попробуйте начать сначала.\nОшибка: {e}")
        return

    async with AsyncSessionLocal() as session:
        stmt = insert(ApartmentTable).values(**new_ad_data.model_dump())
        await session.execute(stmt)
        await session.commit()

    await message.reply("✅ Объявление успешно добавлено!")
    await state.clear()
