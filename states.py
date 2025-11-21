# !!! Упростите класс состояний, как мы обсуждали ранее (для ясности):
from aiogram.fsm.state import StatesGroup, State


class RentStates(StatesGroup):
    main_menu = State()
    viewing_flats = State()
    submitting_offer = State()
    rent_apartment = State()
    viewing_ads = State()

    location = State()
    price = State()
    description = State()
    tel = State()