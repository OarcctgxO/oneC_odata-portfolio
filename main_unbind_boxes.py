import asyncio

from patcher.box_binder import get_boxes_by_cell, bind_box_by_order_ref, get_order_guid_by_num
from http_and_paths.http_and_paths import progress_printer


async def main():
    while True:
        cell = input("Введи ячейку с контейнерами, которые нужно отвязать от заказа / привязать к заказу. Нельзя вводить ШК, только реквизит 'Код': ")
        try:
            boxes = await get_boxes_by_cell(cell)
            print(f"Найдено контейнеров в ячейке: {len(boxes)}")
            print(*[box["Description"] for box in boxes], sep='\n')
            break
        except Exception as er:
            print(str(er))
            print("Ячейка не найдена!")
            continue
    
    while True:
        order_num = input("Введи номер заказа на отгрузку для привязки. Для отвязки ничего не вводи и нажми Enter: ")
        try:
            if order_num:
                order_ref = await get_order_guid_by_num(order_num)
                break
            else:
                order_ref = "00000000-0000-0000-0000-000000000000"
                break
        except Exception as er:
            print(str(er))
            print("Заказ не найден!")
            continue

    
    tasks = []
    for box in boxes:
        task = asyncio.create_task(bind_box_by_order_ref(box["Ref_Key"], order_ref))
        tasks.append(task)
    await progress_printer(tasks)


if __name__ == '__main__':
    asyncio.run(main())