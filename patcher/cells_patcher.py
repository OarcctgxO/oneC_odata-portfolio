from http_and_paths.http_and_paths import http_request_json
from config.config import CATALOG_CELLS


def cell_params_for_get():
    select_params = ','.join([
        "Code",
        "Ref_Key",
        "Помещение",
        "Проезд",
        "Стеллаж",
        "Ярус",
        "Позиция",
        "ПоследовательностьРазмещения",
        "ПоследовательностьОбходаПриРазмещении",
        "ПоследовательностьОбходаПриОтборе",
        "ПоследовательностьОбходаПриИнвентаризации",
        "СтатусЯчейки",
        "Штрихкод",
        "Зона/Description"
    ])

    params = {
        "$format": "application/json;odata=nometadata",
        "$expand": "Зона",
        "$select": select_params
    }

    return params


async def get_cell_by_name(cell_name:str):
    path_url = CATALOG_CELLS
    
    params = cell_params_for_get()
    params["$filter"] = f"Code eq '{cell_name}'"

    result = await http_request_json(method='get', path_url=path_url, params=params)

    if isinstance(result, dict):
        for cell in result['value']:
            if cell['Code'] == cell_name:
                #write_json(cell)
                return cell
    else:
        raise TypeError("Ошибка получения ячейки!")


async def get_cell_by_guid(cell_guid:str):
    path_url = f"{CATALOG_CELLS}(guid'{cell_guid}')"
    
    params = cell_params_for_get()

    result = await http_request_json(method='get', path_url=path_url, params=params)

    if isinstance(result, dict):
        for cell in result['value']:
            if cell['Ref_Key'] == cell_guid:
                #write_json(cell)
                return cell
    else:
        raise TypeError("Ошибка получения ячейки!")


async def get_cell_guid_by_name(cell_name: str):
    cell = await get_cell_by_name(cell_name)

    if isinstance(cell, dict):
        return cell['Ref_Key']
    else:
        raise TypeError("Ошибка получения guid ячейки!")


async def patch_cell_by_name(cell_name: str, data: dict):
    cell_guid = await get_cell_guid_by_name(cell_name)
    await patch_cell_by_guid(cell_guid, data)


async def patch_cell_by_guid(cell_guid: str, data: dict, *args):
    path_url = f"{CATALOG_CELLS}(guid'{cell_guid}')"

    params = {
        "$format": "application/json;odata=nometadata",
    }
    
    #результат неинтересен
    return await http_request_json(method="patch", path_url=path_url, params=params, data=data)


async def get_cells_by_driveway(driveway: str) -> list[dict]:
    path_url = CATALOG_CELLS
    params = cell_params_for_get()
    params["$filter"] = f"Проезд eq '{driveway}'"

    result = await http_request_json(method='get', path_url=path_url, params=params)
    approved_results = []
    if isinstance(result, dict):
        for cell in result['value']:
            if cell["Проезд"] == driveway:
                approved_results.append(cell)
    else:
        raise TypeError("Ошибка получения ячеек!")
    #Может быть пустым
    return approved_results
