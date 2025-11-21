from aiogram import types


# Функция для создания главного меню
def get_main_menu_keyboard():
    builder = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="🏠 Снять квартиру"),
                types.KeyboardButton(text="🔑 Сдать квартиру")
            ],
            [
                types.KeyboardButton(text="🔍 Мои объявления")
            ]
        ],
        resize_keyboard=True
    )
    return builder