from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

class Order:
    """Класс для представления заказа"""
    def __init__(self, id, order_number, timestamp=None, expected_complete=None, status="Не определен", created_at=None):
        self.id = id
        self.order_number = order_number
        self.timestamp = timestamp
        self.expected_complete = expected_complete
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
    def __init__(self, id, omsid, token, gln=""):
        self.id = id
        self.omsid = omsid
        self.token = token
        self.gln = gln

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
    """Класс для представления информации о стране
    
    Attributes:
        id (int): ID страны
        code (str): Код страны
        name (str): Название страны
    """
    
    def __init__(self, id: int, code: str, name: str):
        self.id = id
        self.code = code
        self.name = name

class OrderStatus:
    """Модель статуса заказа"""
    def __init__(self, id: int, code: str, name: str, description: str = ""):
        self.id = id
        self.code = code
        self.name = name
        self.description = description

class APIOrder:
    """Модель для представления заказов из API"""
    def __init__(self, order_id: str, order_status: str, created_timestamp: str,
                 total_quantity: int, num_of_products: int, product_group_type: str,
                 signed: bool, verified: bool, buffers: List = None, 
                 order_status_description: str = None, updated_at: str = None):
        self.order_id = order_id
        self.order_status = order_status
        self.order_status_description = order_status_description
        self.created_timestamp = created_timestamp
        self.total_quantity = total_quantity
        self.num_of_products = num_of_products
        self.product_group_type = product_group_type
        self.signed = signed
        self.verified = verified
        self.buffers = buffers or []
        self.updated_at = updated_at
        self.id = None  # ID в локальной базе данных 

class AggregationFile:
    """Модель файла агрегации"""
    def __init__(self, id: int, filename: str, product: str, marking_codes: List[str], 
                 level1_codes: List[str], level2_codes: List[str], comment: str = "", 
                 json_content: str = "", created_at: datetime = None, data: Dict = None,
                 report_id: str = None, aggregation_report_id: str = None,
                 report_status: str = None, aggregation_status: str = None):
        self.id = id
        self.filename = filename
        self.product = product
        self.marking_codes = marking_codes or []
        self.level1_codes = level1_codes or []
        self.level2_codes = level2_codes or []
        self.comment = comment or ""
        self.json_content = json_content or ""
        self.created_at = created_at
        self.data = data or {}
        self.report_id = report_id or ""
        self.aggregation_report_id = aggregation_report_id or ""
        self.report_status = report_status or ""
        self.aggregation_status = aggregation_status or ""

class UsageType:
    """Класс для представления информации о типе использования кодов маркировки
    
    Attributes:
        id (int): ID типа использования
        code (str): Код типа использования
        name (str): Название типа использования
        description (str): Описание типа использования
    """
    
    def __init__(self, id: int, code: str, name: str, description: str = None):
        self.id = id
        self.code = code
        self.name = name
        self.description = description 

class ReportStatus:
    """Справочник статусов отчетов"""
    PENDING = "PENDING"  # Отчет находится в ожидании
    READY_TO_SEND = "READY_TO_SEND"  # Отчет готов к отправке
    REJECTED = "REJECTED"  # Отчет отклонен
    SENT = "SENT"  # Отчет отправлен
    
    @classmethod
    def get_description(cls, status):
        """Возвращает описание статуса отчета на русском языке"""
        descriptions = {
            cls.PENDING: "Отчет находится в ожидании",
            cls.READY_TO_SEND: "Отчет готов к отправке",
            cls.REJECTED: "Отчет отклонен",
            cls.SENT: "Отчет отправлен"
        }
        return descriptions.get(status, f"Неизвестный статус ({status})") 