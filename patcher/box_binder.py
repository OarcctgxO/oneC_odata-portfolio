import asyncio

from http_and_paths.http_and_paths import write_json, http_request_json, close_session
from utils import get_order_guid_by_num
from config.config import *


def box_params_for_get():
    select_params = ','.join([
        "Ref_Key",
        "Description",
        "Штрихкод",
        "Состояние",
        "Упакован",
        "ДокументПривязки", #не позволяет получить number отдельно, только так!!!!
        "Статус/Description",
        "Статус/Ref_Key"
    ])

    params = {
        "$format": "application/json;odata=nometadata",
        "$expand": "ДокументПривязки,Статус",
        "$select": select_params
    }

    return params


def filter_binded_doc(json_response: dict):
    if "ДокументПривязки_Expanded" in json_response:
        select = [
            "Ref_Key",
            "Number"
        ]
        
        json_response["ДокументПривязки"] = json_response["ДокументПривязки_Expanded"]
        del json_response["ДокументПривязки_Expanded"]
        all_keys = list(json_response["ДокументПривязки"].keys())
        for key in all_keys:
            if key not in select:
                del json_response["ДокументПривязки"][key]
        
        return json_response
    else:
        return json_response


async def get_box_by_name(box_name:str) -> dict | None:
    path_url = CATALOG_BOXES
    
    params = box_params_for_get()
    params["$filter"] = f"startswith(Description,'{box_name}')"

    result = await http_request_json('get', path_url=path_url, params=params)
    #write_json("test_box.json", result)
    if isinstance(result, dict):
        for box in result['value']:
            if box['Description'] == box_name:
                return filter_binded_doc(box)
    else:
        raise TypeError("Ошибка получения контейнера!")


async def get_box_by_guid(box_guid:str) -> dict:
    path_url = f"{CATALOG_BOXES}(guid'{box_guid}')"
    
    params = box_params_for_get()

    result = await http_request_json('get', path_url=path_url, params=params)

    if isinstance(result, dict):
        for box in result['value']:
            if box['Ref_Key'] == box_guid:
                return filter_binded_doc(box)
        return {}
    else:
        raise TypeError("Ошибка получения контейнера!")


async def get_box_guid_by_name(box_name: str):
    box = await get_box_by_name(box_name)

    if isinstance(box, dict):
        return box['Ref_Key']
    else:
        raise TypeError("Ошибка получения guid контейнера!")


async def patch_cell_by_name(box_name: str, data: dict):
    box_guid = await get_box_guid_by_name(box_name)
    await patch_box_by_guid(box_guid, data)


async def patch_box_by_guid(box_guid: str, data: dict) -> dict:
    path_url = f"{CATALOG_BOXES}(guid'{box_guid}')"

    params = {
        "$format": "application/json;odata=nometadata",
    }
    
    #результат неинтересен
    return await http_request_json(method="patch", path_url=path_url, params=params, data=data)


async def get_cell_guid_by_name(cell_name: str):
    path_url = CATALOG_CELLS
    
    params = {
        "$format": "application/json",
        "$filter": f"Code eq '{cell_name}'"
    }

    result = await http_request_json('get', path_url=path_url, params=params)
    return result['value'][0]['Ref_Key']


async def get_boxes_by_cell(cell_name: str):
    path_url = REGISTER_BOX_POSITIONS

    params = {
        "$format": "application/json;odata=nometadata",
        "$expand": "Контейнер/ДокументПривязки,Ячейка",
        "$filter": f"Ячейка eq cast(guid'{await get_cell_guid_by_name(cell_name)}','Catalog_усЯчейки')"
    }

    result = await http_request_json('get', path_url=path_url, params=params)
    #return result
    # WIP
    approved_results = []
    if isinstance(result, dict):
        for box_data in result['value']:
            if box_data["Ячейка_Expanded"]["Code"] == cell_name:
                box = box_data["Контейнер"]
                approved_results.append(filter_binded_doc(box))
        return approved_results
    else:
        raise TypeError("Ошибка получения положения контейнеров!")


async def bind_box_by_order_ref(box_guid: str, order_ref: str | None = None):
    data = {
        "ДокументПривязки_Type": DOC_TYPE_ORDER,
        "ДокументПривязки": order_ref,
    }
    
    return await patch_box_by_guid(box_guid, data=data)