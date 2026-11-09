import asyncio

from http_and_paths.http_and_paths import get_path, write_json, progress_printer
from patcher.cells_patcher import get_cells_by_driveway, patch_cell_by_guid
from config.config import GOOD_ZONES


async def optimize_picking_route():
    """
    Переписывает последовательность отбора в хранении.
    Использует patch-запросы.
    Ссылается на файл driveways_stacks.txt, в котором описана последовательность стеллажей и проездов.
    """
    driveways = {}
    with open(get_path() / "driveways_stacks.txt", 'r', encoding='utf-8') as file:
        last_dw = ""
        for line in file:
            if not line:
                continue
            if len(line.split()) < 2:
                last_dw = line.strip()
            else:
                nums = tuple([int(s) for s in line.split()])
                driveways.setdefault(last_dw, []).append(nums)

    mapping = {}
    count = 5_000
    for driveway, stack_pairs in driveways.items():
        for stack_pair in stack_pairs:
            for stack in stack_pair:
                mapping.setdefault(driveway, {})[stack] = count
            count += 5
    #write_json("picking-py.json",mapping)
    cells_raw = await asyncio.gather(*[get_cells_by_driveway(dw) for dw in mapping])
    cells = []
    for lst in cells_raw:
        cells.extend(lst)

    tasks = []
    for cell in cells:
        try:
            zone = cell["Зона"]["Description"]
            if zone[:3] not in GOOD_ZONES:
                pass
                continue

            driveway = cell["Проезд"]
            if (driveway in ["2A", "2B"]) and (int(cell["Ярус"]) >= 4):
                pass
                continue

            guid = cell["Ref_Key"]
            stack = int(cell["Стеллаж"])

            current_priority = cell["ПоследовательностьОбходаПриОтборе"]
            if int(current_priority) == mapping[driveway][stack]:
                pass
                continue

            data = {"ПоследовательностьОбходаПриОтборе": mapping[driveway][stack]}
            tasks.append(asyncio.create_task(patch_cell_by_guid(guid, data)))
        except KeyError:
            continue

    all = len(tasks)
    await progress_printer(tasks)

if __name__ == '__main__':
    asyncio.run(optimize_picking_route())