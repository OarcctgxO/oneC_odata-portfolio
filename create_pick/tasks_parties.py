from async_lru import alru_cache

import asyncio

from http_and_paths.http_and_paths import http_request_json, progress_printer
from utils import get_order_guid_by_num, format_date
from config.config import *

existing_task_statuses = ['КВыполнению', 'Получена', 'ВРаботе']

# Alias for backwards compatibility
now = format_date


async def task_data_for_post(party_data: dict, order_ref: str):
    data = {
            "Date": now(),
            "Posted": False,
            "ТипЗадачи": "Отбор",
            "Статус": "Новая",
            "Важность": "Обычная",
            "ДокументОснование_Type": DOC_TYPE_ORDER,
            "ДокументОснование": order_ref,
            "НачальнаяЗона_Key": party_data['zone']['Ref'],
            "НачальнаяЯчейка_Key": party_data['cell']['Ref'],
            "НачальныйКонтейнер_Key": party_data['box']['Ref'],
            "ТекущаяЗона_Key": party_data['zone']['Ref'],
            "ТекущаяЯчейка_Key": party_data['cell']['Ref'],
            "ТекущийКонтейнер_Key": party_data['box']['Ref'],
            "Комментарий": "Спланировано через OData.",
            "Номенклатура_Key": party_data['nomen']['Ref'],
            "ПартияНоменклатуры_Key": party_data['party']['Ref'],
            "УпаковкаНоменклатуры_Key": party_data['package']['Ref'],
            "СтатусНоменклатуры_Key": party_data['status_nomen']['Ref'],
            "Количество": party_data["party"]['Amount'],
            "КоличествоУпаковок": (party_data["party"]['Amount']) / (await get_package_num(party_data['package']['Ref'])),
            "КонечнаяЗона_Key": DEFAULT_PICK_ZONE_KEY,
            "КонечнаяЯчейка_Key": DEFAULT_PICK_CELL_KEY,
        }
    #print(data["ДокументОснование_Key"])

    return data


@alru_cache(None)
async def get_package_num(package_ref: str) -> int:
    path_url = f"{CATALOG_PACKAGES}(guid'{package_ref}')"
    params = {"$format": "application/json;odata=nometadata"}

    result = await http_request_json('get', path_url=path_url, params=params)

    return result["Коэффициент"]


async def get_task_by_party_id(party_id:str):
    path_url = DOC_TASK_MOVE_GOOD
    
    params = {
        "$format": "application/json;odata=nometadata",
        "$filter": f"startswith(ПартияНоменклатуры/ID,'{party_id}')",
        "$expand": "ПартияНоменклатуры",
    }

    result = await http_request_json(method='get', path_url=path_url, params=params)
    #return result
    if isinstance(result, dict):
        for task in result['value']:
            if task['ПартияНоменклатуры']['ID'] == party_id and task["Статус"] in existing_task_statuses:
                #write_json(task)
                return task
    else:
        raise TypeError("Ошибка получения задачи!")
    return None


async def post_task_party(party: dict, order_ref: str):
    path_url = DOC_TASK_MOVE_GOOD
    
    params = {"$format": "application/json;odata=nometadata"}
    data = await task_data_for_post(party, order_ref)
    result = await http_request_json("post", path_url=path_url, params=params, data=data)
    return result


async def get_order_by_num(order_num: str):
    """
    Возвращает полный объект заказа по его номеру.
    Использует get_order_guid_by_num из utils для получения GUID.
    """
    order_guid = await get_order_guid_by_num(order_num)
    path_url = f"{DOC_ORDER}(guid'{order_guid}')"
    
    params = {
        "$format": "application/json;odata=nometadata"
    }

    result = await http_request_json('get', path_url=path_url, params=params)
    return result


async def cancel_new_tasks_goods():
    path_url = DOC_TASK_MOVE_GOOD
    params = {
        "$format": "application/json",
        "$filter": "Статус eq 'Новая' and ТипЗадачи eq 'Отбор' and startswith(Комментарий,'Спланировано через OData.')", #Cтатус eq 'Новая' and
    }

    result = await http_request_json(method='get', path_url=path_url, params=params)
    del params["$filter"]
    tasks = []
    if result.get('value', None) is None:
        return None
    while result['value']:
        task_data = result['value'].pop()
        ref = task_data['Ref_Key']
        task_cancel = asyncio.create_task(http_request_json('patch', path_url + f"(guid'{ref}')", params, {"Статус": "Отменена"}))
        tasks.append(task_cancel)
    return tasks