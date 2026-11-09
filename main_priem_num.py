from async_lru import alru_cache

import asyncio
import sys

from http_and_paths.http_and_paths import write_json, progress_printer, http_request_json, get_path
from config.config import DOC_OP, CATALOG_NOMEN


def number_to_str(num: int):
    s = str(num)
    l = len(s)
    add = ''
    if l < 11:
        add = '0' * (11 - l)
    return add + s


async def get_priem():
    path_url = DOC_OP
    
    params = {
        "$format": "application/json;odata=nometadata",
        "$select": "Ref_Key,Number",#Комментарий",
        #"$top": "1",
        #"$skip": "15214",
        "$inlinecount": "allpages",
    }

    result = await http_request_json('get', path_url=path_url, params=params)
    #result = [num['Number'] for num in result['value']]
    #result.sort()
    #return result
    l = int(result["odata.count"])
    
    params = {"$format": "application/json"}
    counter = 1
    tasks = []
    for priem in result['value']:
        data = {
            "Number": number_to_str(counter),
            #"Комментарий": priem['Комментарий'] + "\n" + f"Перенумерованная ОПа, старый номер: '{priem['Number']}'"
        }
        path = path_url + f"(guid'{priem['Ref_Key']}')"
        task = asyncio.create_task(http_request_json('patch', path_url=path, params=params, data=data))
        tasks.append(task)
        counter += 1

    await progress_printer(tasks)
    for task in tasks:
        if task.exception():
            await task
    return result


@alru_cache(None)
async def get_nomen_by_kis(kis: str):
    path_url = CATALOG_NOMEN
    params = {
        "$format": "application/json",
        "$select": "КодКИС,скВидНосителя",
        "$filter": f"startswith(КодКИС,'{kis}')"
    }
    
    result = await http_request_json(method='get', path_url=path_url, params=params)
    
    for nomen in result['value']:
        kis_got = nomen['КодКИС']
        if kis_got == kis:
            return nomen['скВидНосителя']


async def write_nomen_tare():
    with open(get_path() / "er.txt", 'r', encoding='utf-8') as file:
        nomen_list = file.read().split()
    nos = {}
    for nomen in nomen_list:
        nos[nomen] = asyncio.create_task(get_nomen_by_kis(nomen))
    for nomen in nos:
        nos[nomen] = await nos[nomen]
    
    with open(get_path() / "er.txt", 'w', encoding='utf-8') as file:
        for nomen in nos:
            file.write(nomen + "\t" + nos[nomen] + '\n')


async def main():
    res = await get_priem()
    write_json("test_priem.json", res)


if __name__ == '__main__':
    asyncio.run(write_nomen_tare())