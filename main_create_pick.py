import asyncio
import sys

from http_and_paths.http_and_paths import progress_printer, write_json, auth
import create_pick.tasks_parties as p
import create_pick.tasks_boxes as b
import create_pick.get_needs as gn


async def main(order_num: str):
    res = await gn.get_boxes_and_parties_to_plan(order_num)
    boxes, parties, order_ref = res
    boxes, parties = boxes, parties
    print(f"К отбору определено контейнеров: {len(boxes)}")
    print(f"К отбору определено партий: {len(parties)}")
    #return
    boxes_tasks = [asyncio.create_task(b.post_task_box(box, order_ref)) for box in boxes]
    parties_tasks = [asyncio.create_task(p.post_task_party(party, order_ref)) for party in parties]
    all_tasks = boxes_tasks + parties_tasks
    await progress_printer(all_tasks)
    await asyncio.gather(*all_tasks)
    #write_json('test_pick.json', res)


async def cancel():
    tasks_goods_coro = p.cancel_new_tasks_goods()
    tasks_boxes_coro = b.cancel_new_tasks_boxes()

    res = await asyncio.gather(tasks_boxes_coro, tasks_goods_coro)
    boxes = res[0] if res[0] is not None else []
    goods = res[1] if res[1] is not None else []

    all_tasks = boxes + goods
    await progress_printer(all_tasks)

if __name__ == "__main__":
    try:
        auth()
    except FileNotFoundError:
        input("ОШИБКА: файл auth.txt не найден. ПРОВЕРЬТЕ наличие файла auth.txt\nEnter для выхода.")
        sys.exit(1)
    except Exception as e:
        input(f"ОШИБКА ЧТЕНИЯ файла авторизации: {e}\nEnter для выхода.")
        sys.exit(1)
        
    order_num = ''
    while ((not order_num.isalnum()) and (len(order_num) <= 9)):
        order_num = input("Введи номер заказа на отгрузку к планированию: ")
    if int(order_num) == 0:
        print("Начинаю отмену задач...")
        asyncio.run(cancel())
    else:
        asyncio.run(main(order_num))
    input('Готово! Нажми Enter для выхода.')