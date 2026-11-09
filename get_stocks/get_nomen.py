from async_lru import alru_cache
from aiohttp.client_exceptions import ClientResponseError

from config.config import CATALOG_NOMEN
from http_and_paths.http_and_paths import http_request_json


def nomen_error_data(error_type: str, nomen_ref: str | None = None):
    return {
        'Kis': error_type,
        'Tare': error_type,
        'Ref': nomen_ref if nomen_ref is not None else error_type,
    }


@alru_cache(None)
async def get_nomen_by_ref(nomen_ref: str):
    path_url = f"{CATALOG_NOMEN}(guid'{nomen_ref}')"
    params = {
        "$format": "application/json",
        "$select": "Ref_Key,КодКИС,скВидНосителя",
    }
    
    error_type = "KeyError"
    result = {}
    try:
        result = await http_request_json(method='get', path_url=path_url, params=params)
    except ClientResponseError as error:
        error_type = f"ClientResponseError: {error.status}"

    res = {}
    res["Kis"] = result.get("КодКИС", error_type)
    res["Tare"] = result.get("скВидНосителя", error_type)
    res['Ref'] = nomen_ref
    return res