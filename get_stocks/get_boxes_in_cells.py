from async_lru import alru_cache
from aiohttp.client_exceptions import ClientResponseError

from http_and_paths.http_and_paths import http_request_json
from get_stocks.get_zones import get_zone_by_guid
from utils import tomorrow_str
from config.config import REGISTER_BOX_POSITIONS


def cell_zone_error_data(error_type: str):
    cell = {
        "Name": error_type,
        "Status": error_type,
        "Ref": error_type,
    }
    zone = {
        "Name": error_type,
        "Ref": error_type
    }
    return cell, zone


@alru_cache(None)
async def get_cell_and_zone_by_box(box_ref: str):
    path_url = f"{REGISTER_BOX_POSITIONS}(Condition='Контейнер_Key eq guid''{box_ref}''')"
    
    params = {
        "$format": "application/json",
        "Period": f"{tomorrow_str()}T00:00:00",
        "$expand": "Ячейка",
        "$select": "Ячейка,КоличествоBalance"
    }


    error_type = "KeyError"
    result = {}
    try:
        result = await http_request_json(method='get', path_url=path_url, params=params)
    except ClientResponseError as error:
        error_type = f"ClientResponseError: {error.status}"
    
    if 'value' not in result:
        return cell_zone_error_data(error_type)
    
    for cell_data in result.get('value', []):

        amount = cell_data.get("КоличествоBalance", 0)
        if int(amount) != 1:
            continue

        cell_name = cell_data.get('Ячейка_Expanded', {}).get('Code',error_type)
        cell_status = cell_data.get('Ячейка_Expanded', {}).get('СтатусЯчейки',error_type)
        cell_ref = cell_data.get('Ячейка_Expanded', {}).get('Ref_Key',error_type)
        zone_ref = cell_data.get('Ячейка_Expanded', {}).get('Зона_Key',error_type)

        if zone_ref != error_type:
            zone = await get_zone_by_guid(zone_ref)
        else:
            zone = cell_zone_error_data(error_type)[1]
        
        cell = {
            "Name": cell_name,
            "Status": cell_status,
            "Ref": cell_ref,
        }
        return cell, zone
    
    return cell_zone_error_data(error_type)