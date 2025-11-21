# Rent_out_an_apartment/db_schemas.py
from pydantic import BaseModel, Field
from typing import Optional

# Схема для создания (ID генерируется БД автоматически)
class ApartmentCreate(BaseModel):
    location: str
    price: int
    description: str
    tel: str

    type_property: str
    rooms: int
    floor: int
    renovation: str

    owner: int
    views_count: int = 0
    # Добавляем поле photos как строку, так как мы храним его через запятую в БД
    photos: Optional[str] = None


# Схема для чтения данных из БД (включает ID)
class ApartmentRead(BaseModel):
    id: int
    location: str
    price: int
    description: str
    tel: str

    type_property: str
    rooms: int
    floor: int
    renovation: str

    views_count: int = 0
    # При чтении из БД photos тоже будет строкой,
    # её нужно будет разделить в коде отображения
    photos: Optional[str] = None


    # Опционально: Конфигурация для работы с ORM объектами SQLAlchemy
    model_config = {"from_attributes": True}

