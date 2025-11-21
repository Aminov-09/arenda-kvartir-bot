def format_ad_caption(ad, index: int) -> str:
    """
    Форматирует данные объявления из объекта SQLAlchemy Row в строку Markdown.
    """

    # Убедитесь, что типы данных соответствуют вашей модели
    # ad должен содержать поля: location, price, description, tel,
    # type_property, rooms, floor, renovation, views_count

    caption = (
        f"📍 **{ad.location}**\n\n"
        f"🏠 **Тип жилья:** {ad.type_property}\n"
        f"🚪 **Комнаты:** {ad.rooms}\n"
        f"🔢 **Этаж:** {ad.floor}\n"
        f"✨ **Ремонт:** {ad.renovation}\n\n"
        f"💰 **Цена:** {ad.price}\n"
        f"📝 **Описание:** {ad.description}\n"
        f"📞 **Телефон:** {ad.tel}\n\n"
        f"Объявление: {index + 1}\n"
        f"Просмотров: {ad.views_count}"
    )
    return caption
