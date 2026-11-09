from async_lru import alru_cache
from aiohttp.client_exceptions import ClientResponseError

from config.config import CATALOG_ZONES
from http_and_paths.http_and_paths import http_request_json


@alru_cache(None)
async def get_zone_by_guid(zone_ref: str):
    path_url = f"{CATALOG_ZONES}(guid'{zone_ref}')"
    
    select_params = ','.join([
        "Ref_Key",
        "Description"
    ])
    
    params = {
        "$format": "application/json",
        "$select": select_params,
    }
    
    error_type = "KeyError"
    result = {}
    try:
        result = await http_request_json(method='get', path_url=path_url, params=params)
    except ClientResponseError as error:
        error_type = f"ClientResponseError: {error.status}"
    
    zone_name = result.get('Description', error_type)

    zone = {
        "Name": zone_name,
        "Ref": zone_ref
    }
    
    return zone