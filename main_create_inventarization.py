import asyncio
from datetime import datetime

from http_and_paths.http_and_paths import close_session, http_request_json, progress_printer, write_json
from patcher.cells_patcher import get_cell_by_name
from config.config import INVENTORY_ALLOWED_ZONES, INVENTORY_BOX_ZONES, DOC_INVENTORY_TASK
from utils import format_date


existing_task_statuses = ['КВыполнению', 'Получена']

# Alias for backwards compatibility
now = format_date


def task_data_for_post(cell_guid: str, is_box_zone: bool):
    data = {
            "Date": now(),
            "Posted": True,
            "ТипЗадачи": "ИнвентаризацияКонтейнеров" if is_box_zone else "ИнвентаризацияСоставаКонтейнеров",
            "Статус": "КВыполнению",
            "Важность": "Обычная",
            "Ячейка_Key": cell_guid,
            "Инвентаризация": True,
            "Комментарий": "Плановая инвентаризация",
        }

    return data


async def get_task_by_name(task_number:str):
    path_url = DOC_INVENTORY_TASK
    
    params = {"$format": "application/json;odata=nometadata"}
    params["$filter"] = f"startswith(Number,'{task_number}')"

    result = await http_request_json(method='get', path_url=path_url, params=params)
    if isinstance(result, dict):
        for task in result['value']:
            if task['Code'] == task_number:
                #write_json(task)
                return task
    else:
        raise TypeError("Ошибка получения задачи!")
    
    
async def check_existing_task(cell_name: str):
    path_url = DOC_INVENTORY_TASK

    params = {
        "$format": "application/json;odata=nometadata",
        "$expand": "Ячейка",
        "$filter": f"startswith(Ячейка/Code,'{cell_name}')"
    }

    result = await http_request_json('get', path_url=path_url, params=params)
    #return result
    
    if isinstance(result, dict):
        for task in result['value']:
            global existing_task_statuses
            if task['Ячейка']['Code'] == cell_name and task['Статус'] in existing_task_statuses:
                return task
        return False
    else:
        raise TypeError(f"Ошибка проверки задач для ячейки {cell_name}.")


async def post_task_by_data(data: dict):
    path_url = DOC_INVENTORY_TASK
    
    params = {"$format": "application/json;odata=nometadata"}
    
    result = await http_request_json("post", path_url=path_url, params=params, data=data)
    
    return result


async def post_task_by_cell_name(cell_name: str):
    exists = await check_existing_task(cell_name)
    if isinstance(exists, dict):
        return exists
    
    allowed_zones = INVENTORY_ALLOWED_ZONES
    box_zones = INVENTORY_BOX_ZONES
    
    cell = await get_cell_by_name(cell_name)
    if cell is None:
        raise TypeError("Не существует такой ячейки!")
    zone_num: str = cell["Зона"]["Description"][:3] # type: ignore
    if zone_num not in allowed_zones:
        raise TypeError(f"Ячейка {cell_name} относится к запрещенной зоне {cell["Зона"]["Description"]}: создание инвентаризации через API отключено!")
    data = task_data_for_post(cell["Ref_Key"],zone_num in box_zones) # type: ignore
    
    return await post_task_by_data(data)


async def main():
    try:
        print("Вставь список ячеек, разделенных пробелами, табуляциями или переносами строк, нажми Enter и введи 'end'.")
        words = []
        while True:
            line = input()
            parts = line.split()
            for word in parts:
                if word == "end":
                    break
                words.append(word)
            else:
                continue
            break
        
        tasks = []
        for word in words:
            task = asyncio.create_task(post_task_by_cell_name(word))
            tasks.append(task)
        await progress_printer(tasks)
        
        for i in range(len(words)):
            word = words[i]
            task: asyncio.Task = tasks[i]

            try:
                result = task.result()
                num = result['Number']
                date = result['Date']
                print(f"Задача для '{word}': номер задачи {num}, дата и время создания: {date}.")
            except Exception as err:
                print(f"Задача для '{word}': Ошибка: {repr(err)}")
            
        input("\nНажмите Enter для завершения...")
    finally:
        await close_session()


if __name__ == '__main__':
    asyncio.run(main())
    #python main_create_inventarization.py