"""
Конфигурация проекта oneC_odata.

Все изменяемые параметры проекта собраны в одном месте.
"""

from enum import Enum

# =============================================================================
# Активная среда (выбор между тремя базами)
# =============================================================================

class ActiveEnvironment(str, Enum):
    """Активная среда для подключения к 1C:WMS.
    
    Варианты:
    - TEST_BOM: Тестовая база BOM (test_warehouse_a)
    - PRD_BOM: Продуктовая база BOM (production_warehouse_a)
    - PRD_TOM: Продуктовая база TOM (production_warehouse_b)
    """
    TEST_BOM = "TEST_BOM"
    PRD_BOM = "PRD_BOM"
    PRD_TOM = "PRD_TOM"

# Выберите активную среду: "TEST_BOM", "PRD_BOM" или "PRD_TOM"
ACTIVE_ENV: ActiveEnvironment = ActiveEnvironment.PRD_BOM


def get_base_url() -> str:
    """
    Возвращает базовый URL в зависимости от активной среды.
    """
    if ACTIVE_ENV == ActiveEnvironment.TEST_BOM:
        return BASE_URL_TEST_BOM
    elif ACTIVE_ENV == ActiveEnvironment.PRD_BOM:
        return BASE_URL_PRD_BOM
    elif ACTIVE_ENV == ActiveEnvironment.PRD_TOM:
        return BASE_URL_PRD_TOM
    else:
        raise ValueError(f"Неизвестная среда: {ACTIVE_ENV}")


# =============================================================================
# 1C:WMS — URL и пути
# =============================================================================

# Условные адреса: перед запуском укажите свои хосты и пути к базам.
HTTP_BOM_HOST_URL: str = "https://wms-a.example.invalid/"
HTTP_TOM_HOST_URL: str = "https://wms-b.example.invalid/"

# Пути к приложениям WMS
PRD_WMS_BOM: str = "production_warehouse_a/"
TEST_WMS_BOM: str = "test_warehouse_a/"
PRD_WMS_TOM: str = "production_warehouse_b/"

# OData путь
ODATA_PATH_URL: str = "odata/standard.odata/"

# Полные базовые URL для OData
BASE_URL_TEST_BOM: str = HTTP_BOM_HOST_URL + TEST_WMS_BOM + ODATA_PATH_URL
BASE_URL_PRD_BOM: str = HTTP_BOM_HOST_URL + PRD_WMS_BOM + ODATA_PATH_URL
BASE_URL_PRD_TOM: str = HTTP_TOM_HOST_URL + PRD_WMS_TOM + ODATA_PATH_URL

# =============================================================================
# Сетевые настройки
# =============================================================================

# Максимальное количество параллельных соединений
CONNECTION_LIMIT: int = 100

# =============================================================================
# Зоны склада
# =============================================================================

# Зоны, разрешённые для отбора
GOOD_ZONES: list[str] = ["411", "412", "423", "424", "425"]

# Зоны, разрешённые для планирования отбора
ALLOWED_ZONES: tuple[str, ...] = ("411", "412", "423", "421")

# Зоны для контейнеров (где хранятся отбираемые контейнеры)
BOX_ZONES: tuple[str, ...] = ("423", "421")

# Зоны, разрешённые для инвентаризации
INVENTORY_ALLOWED_ZONES: list[str] = ["410", "411", "412", "420", "421", "422", "423", "424", "425"]

# Зоны контейнеров для инвентаризации
INVENTORY_BOX_ZONES: list[str] = ["423", "421", "420", "422", "424"]

# =============================================================================
# Конечные точки для задач отбора
# =============================================================================

# Замените <PICK_ZONE_GUID> и <PICK_CELL_GUID> на свои GUID.
# GUID зоны консолидации (конечная зона)
DEFAULT_PICK_ZONE_KEY: str = "<PICK_ZONE_GUID>"

# GUID ячейки консолидации (конечная ячейка, <PICK_CELL_CODE>)
DEFAULT_PICK_CELL_KEY: str = "<PICK_CELL_GUID>"

# =============================================================================
# OData — имена каталогов и регистров
# =============================================================================

# Каталог: Контейнеры
CATALOG_BOXES: str = "Catalog_усКонтейнеры"

# Каталог: Зоны
CATALOG_ZONES: str = "Catalog_усЗоны"

# Каталог: Ячейки
CATALOG_CELLS: str = "Catalog_усЯчейки"

# Каталог: Номенклатура
CATALOG_NOMEN: str = "Catalog_усНоменклатура"

# Каталог: Упаковки номенклатуры
CATALOG_PACKAGES: str = "Catalog_усУпаковкиНоменклатуры"

# Регистр: Остатки товаров
REGISTER_STOCKS: str = "AccumulationRegister_усОстаткиТоваров/Balance"

# Регистр: Положение контейнеров
REGISTER_BOX_POSITIONS: str = "AccumulationRegister_усПоложениеКонтейнеров/Balance"

# Регистр: Контроль отгрузки
REGISTER_ORDER_CONTROL: str = "AccumulationRegister_усКонтрольОтгрузки_RecordType"

# Документ: Заказ на отгрузку
DOC_ORDER: str = "Document_усЗаказНаОтгрузку"

# Документ: Задачи по перемещению контейнеров
DOC_TASK_MOVE_BOX: str = "Document_усЗадачаПеремещениеКонтейнера"

# Документ: Задачи по перемещению товаров
DOC_TASK_MOVE_GOOD: str = "Document_усЗадачаПеремещениеТовара"

# Документ: Действие по перемещению товара
DOC_ACTION_MOVE_GOOD: str = "Document_усДействиеПоПеремещениюТовара"

# Документ: Задача пересчет (инвентаризация)
DOC_INVENTORY_TASK: str = "Document_усЗадачаПересчет"

# Документ: Ожидаемая приёмка
DOC_OP: str = "Document_усОжидаемаяПриемка"

# =============================================================================
# OData — суффиксы типов для DocumentОснование_Type
# =============================================================================

DOC_TYPE_ORDER: str = "StandardODATA." + DOC_ORDER
DOC_TYPE_TASK_MOVE_GOOD: str = "StandardODATA." + DOC_TASK_MOVE_GOOD
