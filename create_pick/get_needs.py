import asyncio
import sys
from os import cpu_count
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

from http_and_paths.http_and_paths import http_request_json
from create_pick.accurate_sum import accurate_sum
from main_get_stocks import get_stocks
from utils import format_date, get_order_guid_by_num
from config.config import *


def is_sublist(list1: list, list2: list):
    """
    Check if list2 is sublist of list1 (no order).
    """
    counter1 = Counter(list1)
    counter2 = Counter(list2)
    
    for element, count in counter2.items():
        if counter1.get(element, 0) < count:
            return False
    return True


def remove_sublist(list1: list, list2: list):
    """
    Remove list2 from list1 (no order).
    """
    for elem in list2:
        list1.remove(elem)
    
    return list1


def del_box_from_stocks(box_ref: str, stocks: dict):
    for kis in stocks:
        for zone in stocks[kis]:
            if box_ref in stocks[kis][zone]:
                del stocks[kis][zone][box_ref]
                return True
    return False


def get_box_info(box_ref: str, stocks: dict):
    for kis in stocks:
        for zone in stocks[kis]:
            if box_ref in stocks[kis][zone]:
                box = {
                    'zone': stocks[kis][zone][box_ref][0]['zone'],
                    'cell': stocks[kis][zone][box_ref][0]['cell'],
                    'box': stocks[kis][zone][box_ref][0]['box'],
                }
                return box


# Re-export from utils for backwards compatibility
get_order_ref_by_num = get_order_guid_by_num


def need_data():
    data = {
        "КоличествоЗапланировано": 0,
        "КоличествоОтгружено": 0,
        "КоличествоСпланировано": 0,
        "КоличествоЗапланированоМин": 0,
        "КоличествоЗапланированоМакс": 0,
        "КоличествоСкорректировано": 0,
        "КоличествоКСортировке": 0,
        "КоличествоВозврат": 0,
        "КоличествоДоступногоПревышения": 0
    }
    return data


async def get_needs_by_order_num(order_num: str):
    if len(order_num) < 9:
        order_num = '0' * (9 - len(order_num)) + order_num
    path_url = REGISTER_ORDER_CONTROL

    params = {
        "$format": "application/json;odata=nometadata",
        "$select": "ЗаказНаОтгрузку/Поклажедатель_Key,Номенклатура/КодКИС,КоличествоЗапланировано,КоличествоСпланировано,КоличествоОтгружено",
        "$expand": "Номенклатура,ЗаказНаОтгрузку",
        "$filter": f"ЗаказНаОтгрузку/Number eq '{order_num}'",
        "$orderby": "Номенклатура/КодКИС asc",
        #"$top": 100,
    }

    result = await http_request_json(method='get',path_url=path_url, params=params)
    #return result
    needs = {}
    for line in result['value']:
        nomen_name = line["Номенклатура"]["КодКИС"]
        needs.setdefault(nomen_name, 0)
        needs[nomen_name] += line["КоличествоЗапланировано"]
        needs[nomen_name] -= line["КоличествоСпланировано"]
        needs[nomen_name] -= line["КоличествоОтгружено"]
    for key in list(needs.keys()):
        if needs[key] <= 0:
            del needs[key]
    
    owner_ref = result['value'][0]['ЗаказНаОтгрузку']['Поклажедатель_Key']
    return owner_ref, needs

async def get_boxes_and_parties_to_plan(order_num: str):
    print(f"Запрос guid заказа №{order_num}")
    order_ref: str = await get_order_ref_by_num(order_num)
    print(f"Получен guid заказа №{order_num}: guid'{order_ref}'")

    print("Запрос потребностей по заказу:")
    owner_ref, needs = await get_needs_by_order_num(order_num)
    if len(list(needs.keys())) == 0:
        print("Нет потребностей - заказ не переведен к планированию или все уже спланировано")
        sys.exit(0)
    print(f"Получены потребности, по заказу, необходимо получить остатки и список привязанных контейнеров.")

    kis_list = list(needs.keys())
    print("Запрос остатков по номенклатурам: ", end='')
    print(*kis_list, sep=', ')
    stocks = await get_stocks(kis_list, output_log=False)
    print("Получены остатки, уточняю потребности...")

    stocks_aggr = {}

    for party in stocks:
        stocks_aggr.setdefault(party['nomen']['Kis'], {}).setdefault(party['zone']['Name'][:3], {}).setdefault(party['box']['Ref'], []).append(party)

    to_remove = []
    for kis in needs:
        if kis in stocks_aggr:
            for zone in stocks_aggr[kis]:
                for box_ref in stocks_aggr[kis][zone]:
                    to_count = False
                    for party in stocks_aggr[kis][zone][box_ref]:
                        if party['box']['Binded'] not in ("00000000-0000-0000-0000-000000000000", ''):
                            to_remove.append(party['box']['Ref'])
                            if party['box']['Binded'] == order_ref:
                                to_count = True
                        break
                    if not to_count:
                        continue
                    box_sum = sum([party['party']['Amount'] for party in stocks_aggr[kis][zone][box_ref]])
                    needs[kis] -= box_sum
                    continue
    
    for kis in needs:
        if kis in stocks_aggr:
            for zone in stocks_aggr[kis]:
                for box_ref in list(to_remove):
                    if box_ref in stocks_aggr[kis][zone]:
                        del stocks_aggr[kis][zone][box_ref]
                        to_remove.remove(box_ref)
    to_remove = []
    for kis in needs:
        if not needs[kis]:
            to_remove.append(kis)
    for kis in to_remove:
        del needs[kis]

    #return needs
    if len(list(needs.keys())) == 0:
        print("Нет потребностей - заказ не переведен к планированию или все уже спланировано")
        sys.exit(0)

    print(f"Получены потребности, необходим отбор по {len(needs.keys())} номенклатур(е/ам)")
    print('Считаю точный подбор...')

    allowed_zones = ALLOWED_ZONES
    box_zones = BOX_ZONES
    cell_status = ('Доступна', )

    filtered_stocks = {}
    for kis in stocks_aggr:
        for zone in stocks_aggr[kis]:
            for box_ref in stocks_aggr[kis][zone]:
                for party in stocks_aggr[kis][zone][box_ref]:

                    cond_owner = party['owner']['Ref'] == owner_ref
                    cond_zone = party['zone']['Name'][:3] in allowed_zones
                    cond_cell = party['cell']['Status'] in cell_status
                    cond_box = party['box']['Status'] == 'Доступен'
                    cond_party = party['party']['Status'] == 'Доступна'
                    cond_nomen = party['nomen']['Kis'] in kis_list
                    cond_minus = party['party']['PlanMinus'] == 0

                    if cond_owner and cond_cell and cond_box and cond_party and cond_nomen and cond_zone and cond_minus:
                        filtered_stocks.setdefault(kis, {}).setdefault(zone, {}).setdefault(box_ref, []).append(party)

    kis_amounts_to_plan = {}
    loop = asyncio.get_running_loop()
    
    pool = ProcessPoolExecutor(cpu_count())
    try:
        for kis in needs:
            try:
                parties_amounts = []
                for zone_ref in filtered_stocks[kis]:
                    for box_ref in filtered_stocks[kis][zone_ref]:
                        for party in filtered_stocks[kis][zone_ref][box_ref]:
                            parties_amounts.append(party['party']['Amount'])
                fut = loop.run_in_executor(pool, accurate_sum, needs[kis], parties_amounts)
                kis_amounts_to_plan[kis] = fut
            except KeyError:
                continue
        if not list(kis_amounts_to_plan.values()):
            print("Не получены остатки ни по одной номенклатуре.")
            sys.exit(0)
        await asyncio.wait(kis_amounts_to_plan.values())
        print('Суммы подсчитаны, собираю данные и передаю контейнеры и партии на отбор...')
        for kis in list(kis_amounts_to_plan.keys()):
            try:
                plan_list = await kis_amounts_to_plan[kis]
                kis_amounts_to_plan[kis] = plan_list
            except ValueError as error:
                print(f"Невозможно спланировать точно: {kis} - {repr(error)}")
                del kis_amounts_to_plan[kis]
                continue
    finally:
        pool.shutdown()

    parties_to_plan = []
    boxes_to_plan = []

    for kis, plan_list in kis_amounts_to_plan.items():
        plan_satisfied = False
        for zone in box_zones:
            if zone in filtered_stocks[kis] and filtered_stocks[kis][zone]:
                box_temp_structure = {}
                for box_ref in filtered_stocks[kis][zone]:
                    lst = [party['party']['Amount'] for party in filtered_stocks[kis][zone][box_ref]]
                    box_temp_structure[box_ref] = {"sum": sum(lst), "list": lst}
                
                sorted_boxes = sorted(box_temp_structure.items(), key=lambda item: item[1]['sum'], reverse=True)
                while sorted_boxes:
                    box_ref, box_data = sorted_boxes.pop(0)
                    if is_sublist(plan_list, box_data['list']):
                        box = get_box_info(box_ref, filtered_stocks)
                        boxes_to_plan.append(box)
                        plan_list = remove_sublist(plan_list, box_data['list'])
                        del_box_from_stocks(box_ref, filtered_stocks)
                        if not plan_list:
                            plan_satisfied = True
                            break
                if plan_satisfied:
                    break
            if plan_satisfied:
                break

    
    for kis, plan_list in kis_amounts_to_plan.items():
        while plan_list:
            plan = plan_list.pop(0)
            plan_satisfied = False
            for zone in allowed_zones:
                if zone in filtered_stocks[kis] and filtered_stocks[kis][zone]:
                    for box in filtered_stocks[kis][zone]:
                        for party in list(filtered_stocks[kis][zone][box]):
                            if party['party']['Amount'] == plan and party not in parties_to_plan:
                                parties_to_plan.append(party)
                                filtered_stocks[kis][zone][box].remove(party)
                                plan_satisfied = True
                                break
                        if plan_satisfied:
                            break
                    if plan_satisfied:
                        break
    
    return boxes_to_plan, parties_to_plan, order_ref