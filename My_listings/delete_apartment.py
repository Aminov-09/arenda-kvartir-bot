# My_listings/delete_apartment.py

from sqlalchemy import select, delete
from database.database import AsyncSessionLocal
from Rent_out_an_apartment.db_models import apartment as ApartmentTable

# !!! ВАЖНО: Укажите правильный путь к вашей модели unique_views !!!
# Например:
from UniqueView.models import unique_views as UniqueViewsTable


async def delete_apartment_by_index(user_id_tg: int, index: int):
    async with AsyncSessionLocal() as session:
        # 1. Находим объявление по индексу и ID владельца
        query_select = select(ApartmentTable.c.id).where(
            ApartmentTable.c.owner == user_id_tg
        ).offset(index).limit(1)

        result = await session.execute(query_select)
        ad = result.first()

        # ad будет иметь вид (id=3,)

        if ad:
            ad_id = ad.id

            # 2. СНАЧАЛА удаляем все связанные записи из таблицы unique_views
            query_delete_views = delete(UniqueViewsTable).where(
                UniqueViewsTable.c.apartment_id == ad_id
            )
            await session.execute(query_delete_views)

            # 3. ТЕПЕРЬ удаляем само объявление из таблицы apartment
            query_delete_apartment = delete(ApartmentTable).where(
                ApartmentTable.c.id == ad_id
            )
            await session.execute(query_delete_apartment)

            await session.commit()
            return True, "Объявление и все связанные просмотры успешно удалены."
        else:
            return False, "Объявление не найдено."

