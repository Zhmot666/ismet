from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

class Order:
    """Класс для представления заказа"""
    def __init__(self, id, order_number, status, created_at):
        self.id = id
        self.order_number = order_number
        self.status = status
        self.created_at = created_at

class Connection:
    """Класс для представления подключения к API"""
    def __init__(self, id, name, url, is_active):
        self.id = id
        self.name = name
        self.url = url
        self.is_active = is_active

class Credentials:
    """Класс для представления учетных данных"""
    def __init__(self, id, omsid, token, connection=None):
        self.id = id
        self.omsid = omsid
        self.token = token
        self.connection = connection  # Необязательное поле, для обратной совместимости

class Nomenclature:
    """Класс для представления номенклатуры"""
    def __init__(self, id, name, gtin, product_group=""):
        self.id = id
        self.name = name
        self.gtin = gtin
        self.product_group = product_group

class Extension:
    """Класс для представления расширения API (категории продукции)"""
    def __init__(self, id, code, name, is_active):
        self.id = id
        self.code = code
        self.name = name
        self.is_active = is_active

@dataclass
class EmissionType:
    """Класс для представления типа эмиссии (способа выпуска товара)"""
    id: int
    code: str
    name: str
    product_group: Optional[str] = None  # Для каких товарных групп доступен (None - для всех)

@dataclass
class Country:
    """Класс для представления страны"""
    id: int
    code: str
    name: str 