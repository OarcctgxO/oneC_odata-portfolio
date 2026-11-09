import xlwings as xw
import re


def paste_data_to_ostatki(row_array: list[tuple[str]]):
    wb: xw.Book
    pattern = r"Остатки.*\.xlsm"
    for book in xw.books:
        if re.search(pattern, book.name):
            wb = book
            break
    else:
        raise KeyError("Подходящей книги не найдено!")
    
    clear_macro = wb.macro("Module1.ОчиститьОстатки")
    clear_macro()
    
    ws = wb.sheets["Остатки"]

    wb.app.screen_updating = False
    try:
        ws.range('A2').value = row_array
    finally:
        wb.app.screen_updating = True
