from aiogram.fsm.context import FSMContext

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from menu.menu_btns import get_main_menu_keyboard

from Rent_out_an_apartment.add_apartment import router as router_add_apartment
from rent_an_apartment.get_apartment import router as router_get_apartment
from My_listings.my_apartments import router as router_my_apartments

from states import RentStates
from dotenv import load_dotenv
import os

load_dotenv()

# Включаем логирование, чтобы видеть информацию о работе бота
logging.basicConfig(level=logging.INFO)

# Замените 'YOUR_API_TOKEN' на ваш токен
TOKEN = os.environ.get("TOKEN")

# Инициализация бота и диспетчера
# Bot отвечает за взаимодействие с Telegram API
# Dispatcher (DP) отвечает за маршрутизацию обновлений (сообщений, команд) к нужным обработчикам
bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- 1. Обработчик /start (Исправлено использование State) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать в сервис аренды квартир в Таджикистане!\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    # Используем скобки () при установке состояния
    await state.set_state(RentStates.main_menu)


# --- Основная функция запуска бота ---

async def main():
    # !!! КЛЮЧЕВОЙ МОМЕНТ: Регистрируем (подключаем) роутер к диспетчеру !!!
    dp.include_router(router_get_apartment)
    dp.include_router(router_add_apartment)
    dp.include_router(router_my_apartments)
    # Удаляет вебхуки перед запуском в режиме long-polling (если вы ранее использовали вебхуки)
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускает процесс поллинга (постоянного запроса обновлений)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот запускается...")
    # Запуск асинхронной функции main()
    asyncio.run(main())
