from sqlalchemy import Table, Column, Integer, BigInteger, DateTime, String, MetaData
from sqlalchemy.sql import func

# Предполагается, что вы где-то определили metadata объект.
# Например, в файле database/base.py:
# metadata = MetaData()
from database.base import metadata

apartment = Table(
    "apartment",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("location", String(255)),  # Рекомендуется указывать длину для String в большинстве БД
    Column("price", Integer),
    Column("description", String(1024)),
    Column("tel", String(20)),

    Column("type_property", String),
    Column("rooms", Integer),
    Column("floor", Integer),
    Column("renovation", String),

    Column("owner", BigInteger),
    Column("views_count", Integer, default=0),

    # Поле "photos" теперь предназначено для хранения строки, разделенной запятыми
    Column("photos", String(2048)),

    # Используем server_default=func.now() для автоматического заполнения БД
    Column("created_at", DateTime, server_default=func.now())
)
#О квартире

#тип жильё
#Количество комнат: 1
#Этаж: 22 из 24
#Ремонт: евро
