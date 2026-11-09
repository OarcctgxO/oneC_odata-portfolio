import asyncio
from datetime import datetime

from http_and_paths.http_and_paths import http_request_json, progress_printer
from get_stocks.get_nomen import get_nomen_by_ref, nomen_error_data
from get_stocks.get_boxes_in_cells import get_cell_and_zone_by_box, cell_zone_error_data
from utils import tomorrow_str
from config.config import REGISTER_STOCKS


async def get_parties_by_kis(kis: str | None = None, future_list: list[asyncio.Future] | None = None):
    path_url = REGISTER_STOCKS
    
    expand_params = ','.join([
        "Контейнер",
        "КлючАналитикиУчетаНоменклатуры/ПартияНоменклатуры/Поклажедатель",
    ])
    
    params = {
        "$format": "application/json",
        "Period": f"{tomorrow_str()}T00:00:00",
        "$expand": expand_params,
        "$filter": "КоличествоПриходBalance eq 0 and КоличествоРасходBalance eq 0" 
    }
    
    if kis:
        path_url += f"(Condition='КлючАналитикиУчетаНоменклатуры/Номенклатура/КодКИС eq ''{kis}''')"
    
    error_type = "KeyError"
    result = {}

    task = asyncio.create_task(http_request_json(method='get', path_url=path_url, params=params))

    if future_list:
        future_list[0].set_result([task])
    
    try:
        result = await task
    except Exception as er:
        error_type = repr(er)

    boxes_in_cells = {}
    nomens = {}
    
    dark_matter = set()
    parties = []


    for party in result.get('value', []):
        try:
            amount = party.get("КоличествоBalance", error_type)
            minus_amount = party.get("КоличествоРасходBalance", error_type)
            key_status_ref = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("СтатусНоменклатуры_Key", error_type)
            package_ref = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("УпаковкаНоменклатуры_Key", error_type)
            box_binded = party.get("Контейнер", {}).get("ДокументПривязки", error_type)
            box_ref = party.get("Контейнер_Key", error_type)
            box_name = party.get("Контейнер", {}).get("Description", error_type)
            box_status = party.get("Контейнер", {}).get("Состояние", error_type)
            nomen_ref = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("Номенклатура_Key", error_type)
            party_ref = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("Ref_Key", error_type)
            party_id = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("ID", error_type)
            party_status = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("СтатусПартии", error_type)
            party_date = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("ДатаПроизводства", error_type)
            owner_name = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("Поклажедатель", {}).get("Description", error_type)
            owner_ref = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("Поклажедатель", {}).get("Ref_Key", error_type)
            erp_status = party.get("КлючАналитикиУчетаНоменклатуры", {}).get("ПартияНоменклатуры", {}).get("СтатусПартии", error_type)
        except AttributeError: # нет партии
            continue
        party_date = datetime.strptime(party_date if party_date != error_type else '2000-01-01T00:00:00', "%Y-%m-%dT%H:%M:%S")
        if not amount:
            continue
        
        if nomen_ref not in nomens and nomen_ref != error_type:
            nomens[nomen_ref] = asyncio.create_task(get_nomen_by_ref(nomen_ref))
        if box_ref not in boxes_in_cells and box_ref != error_type:
            boxes_in_cells[box_ref] = asyncio.create_task(get_cell_and_zone_by_box(box_ref))
        
        part = {
            "zone": None,
            "owner": {
                "Name": owner_name,
                "Ref": owner_ref
            },
            "cell" : None,
            "box": {
                "Name": box_name,
                "Ref": box_ref,
                "Status": box_status,
                "Binded": box_binded,
            },
            "nomen": nomen_ref,
            "party": {
                "ID": party_id,
                "Ref": party_ref,
                "Amount": amount,
                "Status": party_status,
                "PlanMinus": minus_amount,
                "DateProduced": party_date,
            },
            "status_nomen": {
                "Ref": key_status_ref
            },
            "package": {
                "Ref": package_ref
            },
        }
        
        parties.append(part)
            
    if boxes_in_cells and nomens and future_list:
        task_list_to_wait: list[asyncio.Task] = list(boxes_in_cells.values())
        task_list_to_wait.extend(nomens.values())

        future_list[1].set_result(task_list_to_wait)
    elif future_list:
        future_list[1].set_result(None)

    for part in parties:
        box_ref = part["box"]["Ref"]
        task_cell_zone = boxes_in_cells.get(box_ref, error_type)
        if task_cell_zone == error_type:
            cell, zone = cell_zone_error_data(error_type)
        else:
            cell, zone = await task_cell_zone
        part['cell'] = cell
        part['zone'] = zone

        nomen_ref = part["nomen"]
        task_nomen = nomens.get(nomen_ref, error_type)
        if task_nomen == error_type:
            nomen = nomen_error_data(error_type, nomen_ref)
        else:
            nomen = await task_nomen
        part['nomen'] = nomen

        if 'error' in cell["Name"].lower():
            dark_matter.add(part["box"]["Name"])

    return parties, dark_matter