# services/view_service.py

from sqlalchemy import select, update

from Rent_out_an_apartment.db_models import apartment
from UniqueView.models import unique_views


# Импортируем обе таблицы (apartment и unique_views) из их файла определения


async def process_unique_view(session, user_id_tg: int, apartment_id: int):
    """
    Проверяет и засчитывает уникальный просмотр объявления, используя SQLAlchemy Core Table objects.
    """

    # 1. Проверяем, был ли этот просмотр уникальным ранее
    # Используем unique_views.c.user_id для доступа к колонкам объекта Table
    stmt = select(unique_views).where(
        unique_views.c.user_id == user_id_tg,
        unique_views.c.apartment_id == apartment_id
    )
    result = await session.execute(stmt)
    existing_view = result.first()

    if existing_view is None:
        # 2. Если это ПЕРВЫЙ просмотр от этого пользователя:

        # Добавляем запись в таблицу уникальных просмотров через INSERT
        insert_stmt = unique_views.insert().values(
            user_id=user_id_tg,
            apartment_id=apartment_id
        )
        await session.execute(insert_stmt)

        # Увеличиваем счетчик просмотров в таблице Apartment через UPDATE
        update_stmt = update(apartment).where(apartment.c.id == apartment_id).values(
            views_count=apartment.c.views_count + 1
        )
        await session.execute(update_stmt)

        # Коммитим обе операции
        await session.commit()
        print(f"Уникальный просмотр засчитан для объявления {apartment_id} пользователем {user_id_tg}")

