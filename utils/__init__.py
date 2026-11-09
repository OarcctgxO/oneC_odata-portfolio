"""
Общие утилиты для проекта.
"""

from datetime import datetime, timedelta

from http_and_paths.http_and_paths import http_request_json


def format_date(d: datetime | None = None) -> str:
    """
    Форматирует дату в формат OData: YYYY-MM-DDTHH:MM:SS
    """
    if d is None:
        d = datetime.now()
    s = str(d.date())
    t = str(d.time().strftime("%H:%M:%S"))
    return s + "T" + t


def tomorrow_str() -> str:
    """
    Возвращает дату завтрашнего дня в формате YYYY-MM-DD.
    """
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


async def get_order_guid_by_num(order_num: str) -> str:
    """
    Возвращает Ref_Key (GUID) заказа на отгрузку по его номеру.
    Если номер короче 9 символов, дополняется ведущими нулями.
    """
    if len(order_num) < 9:
        order_num = "0" * (9 - len(order_num)) + order_num

    path_url = "Document_усЗаказНаОтгрузку"

    params = {
        "$format": "application/json;odata=nometadata",
    }
    params["$filter"] = f"startswith(Number,'{order_num}')"

    result = await http_request_json('get', path_url=path_url, params=params)

    for order in result['value']:
        if order['Number'] == order_num:
            return order["Ref_Key"]

    raise ValueError(f"Заказ с номером '{order_num}' не найден!")
