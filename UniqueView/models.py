from sqlalchemy import Table, Column, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.sql import func

from database.base import metadata

unique_views = Table(
    'unique_views',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', BigInteger), # ID пользователя Telegram (BigInteger, как owner)
    Column('apartment_id', Integer, ForeignKey('apartment.id')), # Ссылка на apartments.id
    Column('timestamp', DateTime, server_default=func.now()), # Время просмотра
)