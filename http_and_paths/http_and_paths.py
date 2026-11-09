import aiohttp
import aiohttp.client_exceptions

import atexit
import threading
from multiprocessing import freeze_support
from urllib.parse import urlencode, quote
import sys
import json
import asyncio
from typing import Any
from pathlib import Path
from functools import lru_cache

from config.config import *
from http_and_paths.dynamic_semaphore import DynamicSemaphore


if getattr(sys, 'frozen', False):
        freeze_support()


@lru_cache(1)
def get_path():
    """
    Определяет путь расположения файла вне зависимости от типа файла (exe или py).
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(sys.modules['__main__'].__file__).parent # type: ignore


dynamic_sema = DynamicSemaphore(CONNECTION_LIMIT)
global_session: aiohttp.ClientSession | None = None
registered_atexit = False


@lru_cache(1)
def auth():
    """
    Возвращает aiohttp.BasicAuth - объект авторизации (требует существования auth.txt в директории).
    auth.txt содержит логин и пароль от 1C:WMS через пробел/табуляцию/перенос строки
    """
    file_auth = get_path() / "auth.txt"
    with open(file_auth, encoding='utf-8') as auth_file:
        login, password = auth_file.read().split()
    return aiohttp.BasicAuth(login, password, encoding='utf-8')


def params_spaces_replacer(path_url: str, params: dict | None):
    """
    aiohttp заменяет пробелы плюсами, odata работает только с %20
    Функция возвращает путь с параметрами, правильно заменяя пробелы
    """
    if not params:
        return path_url
    
    # urlencode по умолчанию делает quote_via=quote_plus (пробелы -> +)
    # Заменяем на quote (пробелы -> %20)
    query_string = urlencode(params, doseq=True, quote_via=quote)
    
    separator = '&' if '?' in path_url else '?'
    return f"{path_url}{separator}{query_string}"


def write_json(file_name: str, json_load: Any):
    """
    Записывает json файл на основе json_load (список или словарь).
    Необходима аккуратность с file_name, нет проверки.
    """
    try:
        content = json.dumps(json_load, indent=4, ensure_ascii=False)
    except (TypeError, ValueError):
        try:
            content = json.dumps([list(part) for part in json_load], indent=4, ensure_ascii=False)
        except (TypeError, ValueError):
            content = str(json_load)
    
    with open(get_path() / file_name, 'w', encoding='utf-8') as file:
        file.write(content)


async def get_session() -> aiohttp.ClientSession:
    """
    Возвращает объект сессии соединения.
    Обеспечивает переиспользование TCP-соединений для новых запросов.
    В конце программы нужно закрыть все соединения через await close_session().
    """
    global global_session
    global registered_atexit
    
    if global_session is None or global_session.closed:
        connector = aiohttp.TCPConnector(
            limit=CONNECTION_LIMIT,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
        )
        global_session = aiohttp.ClientSession(
            connector=connector,
            auth=auth()
        )
    
    if not registered_atexit:
        atexit.register(_sync_close_session)
        registered_atexit = True

    return global_session


async def close_session():
    """
    Закрывает все TCP-соединения с базой.
    """
    global global_session
    global registered_atexit
    
    if global_session and not global_session.closed:
        await global_session.close()
        global_session = None

    registered_atexit = False
    print('Все сессии закрыты!')


def _sync_close_session():
    """Гарантированно закрывает сессию при любом завершении программы."""
    print('Запуск финализатора сессий')
    try:
        if sys.is_finalizing():
            return
        if threading.current_thread() is not threading.main_thread():
            return
        asyncio.run(close_session())
    except RuntimeError:
        pass
    except Exception:
        pass


async def http_request_json(method: str, path_url: str, params: dict | None = None, data: dict | None = None) -> dict:
    """
    Основная корутина, для отправки запроса и получения ответа.
    Автоматически сужает семафор при перегрузке сервера (HTTP 503)

    Все еще в разработке.
    """
    new_url = params_spaces_replacer(path_url, params)
    methods = {
        "get": aiohttp.ClientSession.get,
        "post": aiohttp.ClientSession.post,
        "put": aiohttp.ClientSession.put,
        "patch": aiohttp.ClientSession.patch,
        "delete": aiohttp.ClientSession.delete,
        "options": aiohttp.ClientSession.options,
    }
    if method in methods:
        method_func = methods[method]
    else:
        raise TypeError("Метод неопределен!")
    
    global dynamic_sema
    
    while True:
        async with dynamic_sema:
            session = await get_session()
            async with method_func(session, url=get_base_url()+new_url, auth=auth(), json=data) as res:
                try:
                    res.raise_for_status()
                    return await res.json(encoding='utf-8')
                except aiohttp.client_exceptions.ContentTypeError:
                    return {"json_decode_error:": await res.text(encoding='utf-8')}
                except aiohttp.ClientResponseError:
                    status = res.status
                    if status == 503:
                        dynamic_sema.change_width(-1)
                        print("ALERT ALERT ALERT 503")
                        await(asyncio.sleep(1))
                    elif status == 404:
                        return {"404": await res.text(encoding='utf-8')}
                    else:
                        try:
                            write_json("error.json", await res.json(encoding='utf-8'))
                        finally:
                            raise
                        

async def progress_printer(task_list: list[asyncio.Task | asyncio.Future]):
    total = len(task_list)
    done = 0
    exc = 0

    print(f"Всего задач: {total}")
    print(f"Готово задач: {done}", end='', flush=True)

    for coro in asyncio.as_completed(task_list):
        try:
            await coro
        except Exception:
            exc += 1
        done += 1
        print(f"\rГотово задач: {done}", end='')

    print(f"\nИз них завершено с ошибкой: {exc}")