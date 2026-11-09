import asyncio

from http_and_paths.http_and_paths import http_request_json, progress_printer, write_json
from patcher.box_binder import get_order_guid_by_num
from config.config import *
from utils import format_date


existing_task_statuses = ['КВыполнению', 'Получена', 'ВРаботе']

# Alias for backwards compatibility
now = format_date


def task_data_for_post(box: dict, order_ref: str):
    data = {
            "Date": now(),
            "Posted": False,
            "ТипЗадачи": "Отбор",
            "Статус": "Новая",
            "Важность": "Обычная",
            "ПлановоеВремя": now(),
            "Контейнер_Key": box['box']['Ref'],
            "НачальнаяЗона_Key": box['zone']['Ref'],
            "НачальнаяЯчейка_Key": box['cell']['Ref'],
            "НачальныйМастерКонтейнер_Key": "00000000-0000-0000-0000-000000000000",
            "ТекущаяЗона_Key": box['zone']['Ref'],
            "ТекущаяЯчейка_Key": box['cell']['Ref'],
            "ТекущийМастерКонтейнер_Key": "00000000-0000-0000-0000-000000000000",
            "СледующаяЗона_Key": "00000000-0000-0000-0000-000000000000",
            "СледующаяЯчейка_Key": "00000000-0000-0000-0000-000000000000",
            "СледующийМастерКонтейнер_Key": "00000000-0000-0000-0000-000000000000",
            "КонечнаяЗона_Key": DEFAULT_PICK_ZONE_KEY,
            "КонечнаяЯчейка_Key": DEFAULT_PICK_CELL_KEY,
            "КонечныйМастерКонтейнер_Key": "00000000-0000-0000-0000-000000000000",
            "ДокументОснование_Type": DOC_TYPE_ORDER,
            "ДокументОснование": order_ref,
            "Комментарий": "Спланировано через OData.",
        }

    return data


async def get_task_box():
    path_url = DOC_TASK_MOVE_BOX
    
    params = {
        "$format": "application/json;odata=nometadata",
        "$inlinecount": "allpages",
        "$top": 100,
        "$skip": 100000,
        #"$filter": "startswith(ТипЗадачи,'Отбор')"
    }

    result = await http_request_json(method='get', path_url=path_url, params=params)
    await get_cell()
    return result


async def get_cell():
    cell_name = "<PICK_CELL_CODE>"
    path_url = CATALOG_CELLS
    params = {
        "$format": "application/json;odata=nometadata",
        "$expand": "Зона",
        "$filter": f"startswith(Code,'{cell_name}')"
    }

    result = await http_request_json(method='get', path_url=path_url, params=params)
    for cell in result['value']:
        if cell['Code'] == cell_name:
            write_json('test_asked_cell.json', cell)
            return


async def post_task_box(box: dict, order_ref: str):
    path_url = DOC_TASK_MOVE_BOX

    params = {"$format": "application/json;odata=nometadata"}

    data = task_data_for_post(box, order_ref)

    result = await http_request_json("post", path_url=path_url, params=params, data=data)
    return result


async def cancel_new_tasks_boxes():
    path_url = DOC_TASK_MOVE_BOX
    params = {
        "$format": "application/json",
        "$filter": "Статус eq 'Новая' and ТипЗадачи eq 'Отбор' and startswith(Комментарий,'Спланировано через OData.')",
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