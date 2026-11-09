import asyncio
import sys

from get_stocks.get_parties import get_parties_by_kis
from http_and_paths.http_and_paths import write_json, progress_printer, auth
from excel_paster.paste_data import paste_data_to_ostatki


async def get_stocks(kis_lst: list[str] | None, output_log: bool = True):
    loop = asyncio.get_running_loop()
    task_list = []
    if kis_lst:
        futures_kis = [[loop.create_future(), loop.create_future()] for _ in kis_lst]
        results = [asyncio.create_task(get_parties_by_kis(kis_lst[i], futures_kis[i])) for i in range(len(kis_lst))]
    else:
        futures_kis = [[loop.create_future(), loop.create_future()]]
        results = [asyncio.create_task(get_parties_by_kis(None, futures_kis[0]))]
    if output_log:
        task_list = []
        for future_pair in futures_kis:
            task_list.extend(await future_pair[0])

        print('Получение данных регистра "Остатки товаров"...')
        await progress_printer(task_list)


        task_list = []
        for future_pair in futures_kis:
            lst = await future_pair[1]
            if lst is not None:
                task_list.extend(lst)

        print('Создаю задачи получения положений контейнеров и подробностей номенклатур...')
        await progress_printer(task_list)
    else:
        pass
    res = []
    dark_matter = set()
    for task_kis in results:
        parties, dm = await task_kis
        dark_matter = dark_matter | dm
        res.extend(parties)
    if output_log:
        write_json("dark_matter.json", list(dark_matter))
    return res
        

if __name__ == '__main__':
    try:
        auth()
    except FileNotFoundError:
        input("ОШИБКА: файл auth.txt не найден. ПРОВЕРЬТЕ наличие файла auth.txt\nEnter для выхода.")
        sys.exit(1)
    except Exception as e:
        input(f"ОШИБКА ЧТЕНИЯ файла авторизации: {e}\nEnter для выхода.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        kis = sys.argv[1:]
    else:
        print('Не передано аргументов. Нужно вернуть все остатки? [д/н]: ', end='')
        while (inp := input()) not in ['д', 'н', 'y', 'n']:
            print('Неверный ввод!')
            print('Не передано аргументов. Нужно вернуть все остатки? [д/н]: ', end='')
        if inp in 'нn':
           sys.exit(0)
        
        kis = None

    parties = asyncio.run(get_stocks(kis))
    lst = []
    if not isinstance(parties, list):
        raise TypeError("Неожиданный результат!")
    for part in parties:
        cell = part['cell']['Name']
        kis = part['nomen']['Kis']
        tare = part['nomen']['Tare']
        box = part['box']['Name']
        amount = part['party']['Amount']
        owner = part['owner']['Name']
        zone = part['zone']['Name']
        party_date = part['party']['DateProduced']
        party_tuple = (cell, kis, tare, box, amount, owner, zone, party_date)
        if 'error' not in str(cell).lower():
            lst.append((cell, kis, tare, box, amount, owner, zone, party_date))
    paste_data_to_ostatki(lst)