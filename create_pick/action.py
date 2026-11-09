import asyncio
from datetime import datetime, timedelta

from http_and_paths.http_and_paths import http_request_json, progress_printer, write_json
from patcher.box_binder import get_order_guid_by_num
from utils import format_date
from config.config import *


def structure(pick_task: dict):
    struct = {
        "Date": format_date(None),
        "Posted": False,
        "Задача": pick_task['Ref_Key'],
        "Задача_Type": DOC_TYPE_TASK_MOVE_GOOD,
        "Контейнер_Key": pick_task["ТекущийКонтейнер_Key"],
        "Номенклатура_Key": pick_task["Номенклатура_Key"],
        "СтатусНоменклатуры_Key": pick_task["СтатусНоменклатуры_Key"],
        "ПартияНоменклатуры_Key": pick_task["ПартияНоменклатуры_Key"],
        "Количество": pick_task["Количество"],
        "Исполнитель_Key": "00000000-0000-0000-0000-000000000000",
        "УпаковкаНоменклатуры_Key": pick_task["УпаковкаНоменклатуры_Key"],
        "КоличествоУпаковок": pick_task["КоличествоУпаковок"],
        "Комментарий": "Спланировано через OData",
        "ЯДРО_Отрезка": False
    }

    return struct


async def get_action():
    path_url = DOC_ACTION_MOVE_GOOD

    params = {
        "$format": "application/json;odata=nometadata",
        "$top": 1,
        "$inlinecount": "allpages"
    }

    result = await http_request_json(method='get',path_url=path_url, params=params)
    count = int(result["odata.count"])

    params = params = {
        "$format": "application/json;odata=nometadata",
        "$skip": count - 1,
        "$top": 1
        #"$inlinecount": "allpages"
    }

    result = await http_request_json(method='get',path_url=path_url, params=params)

    return result


async def post_action_by_task(pick_task:dict):
    path_url = DOC_ACTION_MOVE_GOOD

    params = {"$format": "application/json"}
    data = structure(pick_task)
    result = await http_request_json("post", path_url=path_url, params=params, data=data)

    ref = result['Ref_Key']

    result = await http_request_json("post", path_url=path_url+f"(guid'{ref}')/Post()", params=params)
    
    result = await http_request_json("get", path_url=path_url+f"(guid'{ref}')", params=params)
    return result