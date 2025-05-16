import requests
import json
from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)

class APIClient:
    """Класс для работы с API"""
    def __init__(self, base_url: str = "http://localhost:8000", extension: str = "pharma", omsid: str = "", db=None, api_logger=None):
        self.base_url = base_url
        self.extension = extension
        self.omsid = omsid
        self.session = requests.Session()
        self.db = db  # Ссылка на базу данных для логирования
        self.api_logger = api_logger
        self.is_api_available = False  # Статус доступности API
        
        # Словарь с русскоязычными описаниями методов API
        self.method_descriptions = {
            # Фармацевтика
            "GET:/api/v2/pharma/ping": "Проверка доступности СУЗ",
            "GET:/api/v2/pharma/version": "Получение версии СУЗ и API",
            "GET:/api/v2/pharma/orders": "Получение списка заказов",
            "GET:/api/v2/pharma/codes": "Получение списка кодов маркировки",
            "GET:/api/v2/pharma/aggregation": "Получение данных агрегации",
            "GET:/api/v2/pharma/report": "Получение отчета СУЗ",
            "POST:/api/v2/pharma/orders": "Отправка заказа на эмиссию КМ",
            "POST:/api/v2/pharma/aggregation": "Отправка данных агрегации",
            "POST:/api/v2/pharma/utilisation": "Отправка отчета о нанесении кодов маркировки",
            
            # Молочная продукция
            "GET:/api/v2/milk/ping": "Проверка доступности СУЗ (молочная продукция)",
            "GET:/api/v2/milk/version": "Получение версии СУЗ и API (молочная продукция)",
            "GET:/api/v2/milk/orders": "Получение списка заказов (молочная продукция)",
            "GET:/api/v2/milk/codes": "Получение списка кодов маркировки (молочная продукция)",
            "GET:/api/v2/milk/aggregation": "Получение данных агрегации (молочная продукция)",
            "GET:/api/v2/milk/report": "Получение отчета СУЗ (молочная продукция)",
            "POST:/api/v2/milk/orders": "Отправка заказа на эмиссию КМ (молочная продукция)",
            "POST:/api/v2/milk/aggregation": "Отправка данных агрегации (молочная продукция)",
            "POST:/api/v2/milk/utilisation": "Отправка отчета о нанесении кодов маркировки (молочная продукция)",
            
            # Табачная продукция
            "GET:/api/v2/tobacco/ping": "Проверка доступности СУЗ (табачная продукция)",
            "GET:/api/v2/tobacco/version": "Получение версии СУЗ и API (табачная продукция)",
            "GET:/api/v2/tobacco/orders": "Получение списка заказов (табачная продукция)",
            "GET:/api/v2/tobacco/codes": "Получение списка кодов маркировки (табачная продукция)",
            "GET:/api/v2/tobacco/aggregation": "Получение данных агрегации (табачная продукция)",
            "GET:/api/v2/tobacco/report": "Получение отчета СУЗ (табачная продукция)",
            "POST:/api/v2/tobacco/orders": "Отправка заказа на эмиссию КМ (табачная продукция)",
            "POST:/api/v2/tobacco/aggregation": "Отправка данных агрегации (табачная продукция)",
            "POST:/api/v2/tobacco/utilisation": "Отправка отчета о нанесении кодов маркировки (табачная продукция)",
            
            # Обувные товары
            "GET:/api/v2/shoes/ping": "Проверка доступности СУЗ (обувь)",
            "GET:/api/v2/shoes/version": "Получение версии СУЗ и API (обувь)",
            "GET:/api/v2/shoes/orders": "Получение списка заказов (обувь)",
            "GET:/api/v2/shoes/codes": "Получение списка кодов маркировки (обувь)",
            "GET:/api/v2/shoes/aggregation": "Получение данных агрегации (обувь)",
            "GET:/api/v2/shoes/report": "Получение отчета СУЗ (обувь)",
            "POST:/api/v2/shoes/orders": "Отправка заказа на эмиссию КМ (обувь)",
            "POST:/api/v2/shoes/aggregation": "Отправка данных агрегации (обувь)",
            "POST:/api/v2/shoes/utilisation": "Отправка отчета о нанесении кодов маркировки (обувь)",
            
            # Алкогольная продукция
            "GET:/api/v2/alcohol/ping": "Проверка доступности СУЗ (алкоголь)",
            "GET:/api/v2/alcohol/version": "Получение версии СУЗ и API (алкоголь)",
            "GET:/api/v2/alcohol/orders": "Получение списка заказов (алкоголь)",
            "GET:/api/v2/alcohol/codes": "Получение списка кодов маркировки (алкоголь)",
            "GET:/api/v2/alcohol/aggregation": "Получение данных агрегации (алкоголь)",
            "GET:/api/v2/alcohol/report": "Получение отчета СУЗ (алкоголь)",
            "POST:/api/v2/alcohol/orders": "Отправка заказа на эмиссию КМ (алкоголь)",
            "POST:/api/v2/alcohol/aggregation": "Отправка данных агрегации (алкоголь)",
            "POST:/api/v2/alcohol/utilisation": "Отправка отчета о нанесении кодов маркировки (алкоголь)",
            
            # Товары легкой промышленности
            "GET:/api/v2/lp/ping": "Проверка доступности СУЗ (легпром)",
            "GET:/api/v2/lp/version": "Получение версии СУЗ и API (легпром)",
            "GET:/api/v2/lp/orders": "Получение списка заказов (легпром)",
            "GET:/api/v2/lp/codes": "Получение списка кодов маркировки (легпром)",
            "GET:/api/v2/lp/aggregation": "Получение данных агрегации (легпром)",
            "GET:/api/v2/lp/report": "Получение отчета СУЗ (легпром)",
            "POST:/api/v2/lp/orders": "Отправка заказа на эмиссию КМ (легпром)",
            "POST:/api/v2/lp/aggregation": "Отправка данных агрегации (легпром)",
            "POST:/api/v2/lp/utilisation": "Отправка отчета о нанесении кодов маркировки (легпром)",
            
            # Питьевая вода
            "GET:/api/v2/water/ping": "Проверка доступности СУЗ (вода)",
            "GET:/api/v2/water/version": "Получение версии СУЗ и API (вода)",
            "GET:/api/v2/water/orders": "Получение списка заказов (вода)",
            "GET:/api/v2/water/codes": "Получение списка кодов маркировки (вода)",
            "GET:/api/v2/water/aggregation": "Получение данных агрегации (вода)",
            "GET:/api/v2/water/report": "Получение отчета СУЗ (вода)",
            "POST:/api/v2/water/orders": "Отправка заказа на эмиссию КМ (вода)",
            "POST:/api/v2/water/aggregation": "Отправка данных агрегации (вода)",
            "POST:/api/v2/water/utilisation": "Отправка отчета о нанесении кодов маркировки (вода)",
            
            # URL с параметрами для фармацевтики
            "GET:/api/v2/pharma/orders?omsId=": "Получение списка заказов по omsId (фарма)",
            "GET:/api/v2/pharma/ping?omsId=": "Проверка доступности СУЗ по omsId (фарма)",
            "GET:/api/v2/pharma/codes?omsId=": "Получение списка кодов маркировки по omsId (фарма)",
            "GET:/api/v2/pharma/aggregation?omsId=": "Получение данных агрегации по omsId (фарма)",
            "GET:/api/v2/pharma/report?omsId=": "Получение отчета СУЗ по omsId (фарма)",
            "POST:/api/v2/pharma/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (фарма)",
            
            # URL с параметрами для молочной продукции
            "GET:/api/v2/milk/orders?omsId=": "Получение списка заказов по omsId (молоко)",
            "GET:/api/v2/milk/ping?omsId=": "Проверка доступности СУЗ по omsId (молоко)",
            "GET:/api/v2/milk/codes?omsId=": "Получение списка кодов маркировки по omsId (молоко)",
            "GET:/api/v2/milk/aggregation?omsId=": "Получение данных агрегации по omsId (молоко)",
            "GET:/api/v2/milk/report?omsId=": "Получение отчета СУЗ по omsId (молоко)",
            "POST:/api/v2/milk/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (молоко)",
            
            # URL с параметрами для табачной продукции
            "GET:/api/v2/tobacco/orders?omsId=": "Получение списка заказов по omsId (табак)",
            "GET:/api/v2/tobacco/ping?omsId=": "Проверка доступности СУЗ по omsId (табак)",
            "GET:/api/v2/tobacco/codes?omsId=": "Получение списка кодов маркировки по omsId (табак)",
            "GET:/api/v2/tobacco/aggregation?omsId=": "Получение данных агрегации по omsId (табак)",
            "GET:/api/v2/tobacco/report?omsId=": "Получение отчета СУЗ по omsId (табак)",
            "POST:/api/v2/tobacco/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (табак)",
            
            # URL с параметрами для обуви
            "GET:/api/v2/shoes/orders?omsId=": "Получение списка заказов по omsId (обувь)",
            "GET:/api/v2/shoes/ping?omsId=": "Проверка доступности СУЗ по omsId (обувь)",
            "GET:/api/v2/shoes/codes?omsId=": "Получение списка кодов маркировки по omsId (обувь)",
            "GET:/api/v2/shoes/aggregation?omsId=": "Получение данных агрегации по omsId (обувь)",
            "GET:/api/v2/shoes/report?omsId=": "Получение отчета СУЗ по omsId (обувь)",
            "POST:/api/v2/shoes/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (обувь)",
            
            # URL с параметрами для алкоголя
            "GET:/api/v2/alcohol/orders?omsId=": "Получение списка заказов по omsId (алкоголь)",
            "GET:/api/v2/alcohol/ping?omsId=": "Проверка доступности СУЗ по omsId (алкоголь)",
            "GET:/api/v2/alcohol/codes?omsId=": "Получение списка кодов маркировки по omsId (алкоголь)",
            "GET:/api/v2/alcohol/aggregation?omsId=": "Получение данных агрегации по omsId (алкоголь)",
            "GET:/api/v2/alcohol/report?omsId=": "Получение отчета СУЗ по omsId (алкоголь)",
            "POST:/api/v2/alcohol/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (алкоголь)",
            
            # URL с параметрами для легкой промышленности
            "GET:/api/v2/lp/orders?omsId=": "Получение списка заказов по omsId (легпром)",
            "GET:/api/v2/lp/ping?omsId=": "Проверка доступности СУЗ по omsId (легпром)",
            "GET:/api/v2/lp/codes?omsId=": "Получение списка кодов маркировки по omsId (легпром)",
            "GET:/api/v2/lp/aggregation?omsId=": "Получение данных агрегации по omsId (легпром)",
            "GET:/api/v2/lp/report?omsId=": "Получение отчета СУЗ по omsId (легпром)",
            "POST:/api/v2/lp/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (легпром)",
            
            # URL с параметрами для воды
            "GET:/api/v2/water/orders?omsId=": "Получение списка заказов по omsId (вода)",
            "GET:/api/v2/water/ping?omsId=": "Проверка доступности СУЗ по omsId (вода)",
            "GET:/api/v2/water/codes?omsId=": "Получение списка кодов маркировки по omsId (вода)",
            "GET:/api/v2/water/aggregation?omsId=": "Получение данных агрегации по omsId (вода)",
            "GET:/api/v2/water/report?omsId=": "Получение отчета СУЗ по omsId (вода)",
            "POST:/api/v2/water/orders?omsId=": "Создание заказа на эмиссию КМ по omsId (вода)"
        }
    
    def get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов к API"""
        client_token = ""
        if self.db:
            credentials = self.db.get_credentials()
            if credentials:
                client_token = credentials[0].token
        
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
            'clientToken': client_token
        }
    
    def log_request(self, method, url, data, response, description=None):
        """Логирование запроса и ответа в базу данных"""
        if self.db:
            try:
                # Преобразуем данные в строки JSON
                request_data = {'data': data}
                
                # Добавляем заголовки запроса, если они были
                if hasattr(response.request, 'headers'):
                    request_data['headers'] = dict(response.request.headers)
                
                request_str = json.dumps(request_data, ensure_ascii=False)
                response_str = json.dumps(response.json(), ensure_ascii=False) if response.content else "{}"
                status_code = response.status_code
                success = 200 <= status_code < 300  # Успешный ответ, если код 2xx
                
                # Получаем описание метода API из словаря по ключу method:url
                # Например: "GET:/api/v2/pharma/version"
                relative_url = url.replace(self.base_url, "")
                
                # Для URL с параметрами, обрезаем всё после базового пути
                # Обработка URL, например, /api/v2/pharma/orders?omsId=12345
                method_key = f"{method}:{relative_url}"
                
                # Список для проверки различных вариантов ключей
                possible_keys = [method_key]
                
                # Для URL с параметрами отдельно проверяем основной путь и основной путь с префиксом параметра
                if "?" in relative_url:
                    base_path = relative_url.split("?")[0]
                    param_prefix = relative_url.split("?")[1].split("=")[0]
                    
                    # Добавляем варианты ключей для поиска
                    possible_keys.append(f"{method}:{base_path}")  # основной путь без параметров
                    possible_keys.append(f"{method}:{base_path}?{param_prefix}=")  # путь с префиксом параметра
                
                # Если описание не передано явно, ищем в словаре
                if description is None:
                    # Проверяем все возможные ключи
                    for key in possible_keys:
                        if key in self.method_descriptions:
                            description = self.method_descriptions[key]
                            break
                    else:
                        # Если ни один ключ не найден, используем заглушку
                        description = f"Запрос {method} {relative_url}"
                
                # Логирование для отладки
                logger.debug(f"URL: {url}, Относительный URL: {relative_url}")
                logger.debug(f"Метод: {method}, Ключ метода: {method_key}")
                logger.debug(f"Проверяемые ключи: {possible_keys}")
                logger.debug(f"Итоговое описание: {description}")
                
                # Проверяем наличие таблицы api_logs перед логированием
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_logs'")
                if not cursor.fetchone():
                    logger.warning("Таблица api_logs не существует. Создаем таблицу...")
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS api_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            method TEXT NOT NULL,
                            url TEXT NOT NULL,
                            request TEXT NOT NULL,
                            response TEXT NOT NULL,
                            status_code INTEGER,
                            success INTEGER DEFAULT 1,
                            description TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    self.db.conn.commit()
                    logger.info("Таблица api_logs создана")
                
                # Проверяем структуру таблицы
                cursor.execute("PRAGMA table_info(api_logs)")
                columns = [col["name"] for col in cursor.fetchall()]
                required_columns = ["method", "url", "request", "response", "status_code", "success", "description", "timestamp"]
                missing_columns = [col for col in required_columns if col not in columns]
                if missing_columns:
                    logger.warning(f"В таблице api_logs отсутствуют колонки: {missing_columns}")
                    # Добавляем недостающие колонки
                    for col in missing_columns:
                        if col == "success":
                            cursor.execute(f"ALTER TABLE api_logs ADD COLUMN {col} INTEGER DEFAULT 1")
                        elif col == "timestamp":
                            cursor.execute(f"ALTER TABLE api_logs ADD COLUMN {col} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                        else:
                            cursor.execute(f"ALTER TABLE api_logs ADD COLUMN {col} TEXT")
                    self.db.conn.commit()
                    logger.info(f"Добавлены недостающие колонки: {missing_columns}")
                
                # Логируем запрос
                try:
                    self.db.add_api_log(
                        method=method,
                        url=url,
                        request=request_str,
                        response=response_str,
                        status_code=status_code,
                        success=success,
                        description=description
                    )
                    logger.info(f"Запрос {method} {url} успешно залогирован")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога API: {str(e)}")
                    # Попробуем упрощенный вариант
                    try:
                        cursor.execute(
                            "INSERT INTO api_logs (method, url, request, response, status_code, success, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (method, url, request_str, response_str, status_code, 1 if success else 0, description)
                        )
                        self.db.conn.commit()
                        logger.info("Запрос залогирован прямым SQL-запросом")
                    except Exception as e2:
                        logger.error(f"Повторная ошибка при логировании API: {str(e2)}")
                
                # Обновляем статус доступности API
                self.is_api_available = success
                
            except Exception as e:
                logger.error(f"Ошибка при логировании запроса: {str(e)}")
    
    def get_description_for_url(self, method, url):
        """Получение описания для метода и URL
        
        Используется для отладки и проверки корректности описаний
        
        Args:
            method (str): HTTP метод (GET, POST и т.д.)
            url (str): Полный URL запроса
            
        Returns:
            str: Русскоязычное описание запроса
        """
        relative_url = url.replace(self.base_url, "")
        method_key = f"{method}:{relative_url}"
        
        # Список для проверки различных вариантов ключей
        possible_keys = [method_key]
        
        # Для URL с параметрами отдельно проверяем основной путь и основной путь с префиксом параметра
        if "?" in relative_url:
            base_path = relative_url.split("?")[0]
            param_prefix = relative_url.split("?")[1].split("=")[0]
            
            # Добавляем варианты ключей для поиска
            possible_keys.append(f"{method}:{base_path}")  # основной путь без параметров
            possible_keys.append(f"{method}:{base_path}?{param_prefix}=")  # путь с префиксом параметра
        
        # Проверяем все возможные ключи
        for key in possible_keys:
            if key in self.method_descriptions:
                return self.method_descriptions[key]
        
        # Если ни один ключ не найден, используем заглушку
        return f"Запрос {method} {relative_url}"
    
    def list_all_descriptions(self):
        """Получение всех доступных описаний методов API
        
        Returns:
            Dict[str, str]: Словарь с ключами методов и их описаниями
        """
        return self.method_descriptions
    
    def export_descriptions_to_file(self, filename="api_descriptions.json"):
        """Сохранение словаря с описаниями методов API в JSON-файл
        
        Args:
            filename (str): Имя файла для сохранения
            
        Returns:
            bool: True, если экспорт прошел успешно, иначе False
        """
        try:
            # Создаем отсортированный словарь для более удобного просмотра
            sorted_descriptions = {}
            # Сначала группируем по расширениям API
            extensions = set()
            for key in self.method_descriptions.keys():
                parts = key.split(":")
                if len(parts) >= 2:
                    url_parts = parts[1].split("/")
                    if len(url_parts) >= 4:
                        extension = url_parts[3]
                        extensions.add(extension)
            
            # Теперь создаем структурированный словарь
            for extension in sorted(extensions):
                sorted_descriptions[extension] = {}
                for key, value in self.method_descriptions.items():
                    if f"/api/v2/{extension}/" in key:
                        sorted_descriptions[extension][key] = value
            
            # Добавляем оставшиеся ключи, которые не попали ни в одну группу
            sorted_descriptions["other"] = {}
            for key, value in self.method_descriptions.items():
                found = False
                for extension in extensions:
                    if f"/api/v2/{extension}/" in key:
                        found = True
                        break
                if not found:
                    sorted_descriptions["other"][key] = value
            
            # Сохраняем в файл с отступами для удобства чтения
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(sorted_descriptions, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"Ошибка при экспорте описаний в файл: {str(e)}")
            return False
    
    def import_descriptions_from_file(self, filename="api_descriptions.json"):
        """Загрузка словаря с описаниями методов API из JSON-файла
        
        Args:
            filename (str): Имя файла для загрузки
            
        Returns:
            bool: True, если импорт прошел успешно, иначе False
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Преобразуем структурированный словарь обратно в плоский
            descriptions = {}
            for extension, extension_descriptions in data.items():
                for key, value in extension_descriptions.items():
                    descriptions[key] = value
            
            # Обновляем словарь описаний
            self.method_descriptions.update(descriptions)
            
            return True
        except Exception as e:
            print(f"Ошибка при импорте описаний из файла: {str(e)}")
            return False
    
    def get_ping(self) -> Dict[str, Any]:
        """Проверка доступности API"""
        url = f"{self.base_url}/api/v2/{self.extension}/ping?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_version(self) -> Dict[str, Any]:
        """Получение версии API"""
        url = f"{self.base_url}/api/v2/{self.extension}/version"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_orders(self) -> Dict[str, Any]:
        """Получение списка заказов"""
        url = f"{self.base_url}/api/v2/{self.extension}/orders?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_orders_status(self) -> Dict[str, Any]:
        """Получение статуса заказов
        
        Этот метод используется для получения статуса заказов с использованием 
        маркера безопасности (token) и идентификатора СУЗ.
        
        Примечания:
        - Метод предназначен для восстановления АСУТП после полной потери данных
        - Использование в штатных процессах работы с СУЗ запрещено
        - Обращение к данному методу возможно не чаще 100 раз в секунду
        
        Returns:
            Dict[str, Any]: Словарь с данными о статусе заказов и идентификаторе СУЗ
        """
        url = f"{self.base_url}/api/v2/{self.extension}/orders?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_codes(self) -> Dict[str, Any]:
        """Получение списка кодов"""
        url = f"{self.base_url}/api/v2/{self.extension}/codes?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_aggregation(self) -> Dict[str, Any]:
        """Получение агрегации"""
        url = f"{self.base_url}/api/v2/{self.extension}/aggregation?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def get_report(self) -> Dict[str, Any]:
        """Получение отчета"""
        url = f"{self.base_url}/api/v2/{self.extension}/report?omsId={self.omsid}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers)
        self.log_request("GET", url, None, response)
        return response.json()
    
    def post_orders(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка заказов"""
        url = f"{self.base_url}/api/v2/{self.extension}/orders"
        headers = self.get_headers()
        response = self.session.post(url, json=data, headers=headers)
        self.log_request("POST", url, data, response)
        return response.json()
    
    def post_aggregation(self, data: Dict[str, Any], custom_extension: str = None) -> Dict[str, Any]:
        """Отправка отчета об агрегации КМ
        
        Формирует и отправляет отчет об агрегации:
        {
            "participantId": "ИНН производителя",
            "productionLineId": "Идентификатор производственной линии",
            "productionOrderId": "Идентификатор производственного заказа",
            "aggregationUnits": [
                {
                    "unitSerialNumber": "Серийный номер единицы агрегации",
                    "aggregationType": "Тип агрегации (AGGREGATION_BOX, AGGREGATION_PALLET и др)",
                    "aggregationUnitCapacity": 20,  # Емкость упаковки
                    "aggregatedItemsCount": 20,     # Количество агрегированных товаров
                    "sntins": ["код1", "код2", ...]  # Списки кодов, включенных в эту единицу агрегации
                },
                ...
            ],
        }
        """
        # Проверяем наличие всех необходимых полей
        if not data or not isinstance(data, dict):
            raise ValueError("Неверный формат данных для отчета об агрегации")
            
        if 'participantId' not in data or not data['participantId']:
            logger.warning("Не указан participantId (ИНН) для отчета об агрегации")
            
        if 'aggregationUnits' not in data or not data['aggregationUnits']:
            raise ValueError("Не указаны единицы агрегации (aggregationUnits) для отчета об агрегации")
        
        # Проверяем наличие productionLineId 
        if 'productionLineId' not in data or not data['productionLineId']:
            logger.warning("Не указан productionLineId (идентификатор производственной линии) для отчета об агрегации")
            
        # Проверяем наличие productionOrderId
        if 'productionOrderId' not in data or not data['productionOrderId']:
            logger.warning("Не указан productionOrderId (идентификатор производственного заказа) для отчета об агрегации")
            
        # Подготавливаем url API
        api_extension = custom_extension or self.extension
        extension_prefix = f"{api_extension}/" if api_extension else ""
        
        if 'omsId' in data and data['omsId']:
            oms_id = data['omsId']
            url = f"{self.base_url}/api/v2/{extension_prefix}aggregation?omsId={oms_id}"
        else:
            url = f"{self.base_url}/api/v2/{extension_prefix}aggregation"
            
        # Делаем копию данных, чтобы не изменять оригинал
        request_data = deepcopy(data)
        
        # Удаляем поля, которые не нужны для API
        if 'omsId' in request_data:
            del request_data['omsId']
        
        if 'file_id' in request_data:
            del request_data['file_id']
        
        # Проверяем и нормализуем aggregationUnits
        for i, unit in enumerate(request_data['aggregationUnits']):
            # Проверяем наличие обязательных полей
            if 'unitSerialNumber' not in unit or not unit['unitSerialNumber']:
                raise ValueError(f"Не указан серийный номер единицы (unitSerialNumber) для единицы агрегации #{i+1}")
                
            if 'aggregationType' not in unit or not unit['aggregationType']:
                logger.warning(f"Не указан тип агрегации (aggregationType) для единицы #{i+1}, устанавливаем AGGREGATION")
                unit['aggregationType'] = "AGGREGATION"
                
            # Проверяем допустимость типа агрегации
            allowed_aggregation_types = ["AGGREGATION", "AGGREGATION_BOX", "AGGREGATION_PALLET", "AGGREGATION_CONTAINER"]
            if unit["aggregationType"] not in allowed_aggregation_types:
                error_msg = f"Недопустимый тип агрегации для единицы #{i+1}: {unit['aggregationType']}. Допустимые значения: {', '.join(allowed_aggregation_types)}"
                logger.error(error_msg)
                # Автоматически исправляем на допустимое значение
                logger.warning(f"Автоматическая замена типа агрегации на AGGREGATION")
                unit["aggregationType"] = "AGGREGATION"  # Всегда используем AGGREGATION
                
            # Проверяем наличие и валидность sntins
            if 'sntins' not in unit or not isinstance(unit['sntins'], list):
                logger.warning(f"Не указаны коды маркировки (sntins) для единицы #{i+1}")
                unit['sntins'] = []
                
            # Нормализуем коды маркировки
            unit['sntins'] = self.normalize_codes(unit['sntins'])
                
            # Проверяем соответствие емкости упаковки и количества кодов
            if 'aggregationUnitCapacity' not in unit or not isinstance(unit['aggregationUnitCapacity'], int):
                logger.warning(f"Не указана емкость упаковки (aggregationUnitCapacity) для единицы #{i+1}")
                # Устанавливаем емкость равной количеству кодов маркировки
                unit['aggregationUnitCapacity'] = len(unit['sntins'])
            elif unit['aggregationUnitCapacity'] != len(unit['sntins']):
                logger.warning(f"Емкость упаковки ({unit['aggregationUnitCapacity']}) не соответствует количеству кодов маркировки ({len(unit['sntins'])}) для единицы #{i+1}. Исправляем.")
                unit['aggregationUnitCapacity'] = len(unit['sntins'])
            
            # Добавляем параметр aggregatedItemsCount с таким же значением как и aggregationUnitCapacity
            unit['aggregatedItemsCount'] = unit['aggregationUnitCapacity']
        
        # Отправляем запрос
        headers = self.get_headers()
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        
        # Напрямую используем json параметр для корректной сериализации
        success, response_data, status_code = self.request(
            method="POST", 
            url=url, 
            data=request_data,  # Будет автоматически сериализовано функцией request
            headers=headers, 
            description="Отправка отчета об агрегации"
        )
        
        # Если статус успешный, возвращаем ответ с индикатором успеха
        if 200 <= status_code < 300:
            response_data['success'] = True
        else:
            response_data['success'] = False
            
        return response_data
    
    def post_utilisation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка данных об использовании (нанесении) КМ
        
        Формирует и отправляет запрос следующего вида:
        {
            "products": [
                {
                    "gtin": "04810155003995",
                    "quantity": 3000,
                    "serialNumberType": "OPERATOR",
                    "templateId": 5
                }
            ],
            "factoryId": "4810155900003",
            "releaseMethodType": "IMPORT",
            "factoryCountry": "BY"
        }
        
        Или для прямого использования кодов (отчет о нанесении):
        {
            "sntins": ["код1", "код2", ...],
            "expirationDate": "2025-12-31",
            "seriesNumber": "001",
            "usageType": "PRINTED"
        }
        
        Важно: omsId должен передаваться в URL-строке запроса, а не в теле запроса.
        
        Args:
            data (Dict[str, Any]): Данные отчета, включающие информацию о продуктах
                                  или кодах маркировки для отчета о нанесении.
                                  
        Returns:
            Dict[str, Any]: Результат отправки отчета о нанесении КМ
            
        Raises:
            ValueError: Если данные не соответствуют требованиям API
            requests.RequestException: Если возникла ошибка при отправке запроса
        """
        # Проверяем наличие токена
        headers = self.get_headers()
        if not headers.get('clientToken'):
            error_msg = "Отсутствует токен аутентификации (clientToken). Необходимо настроить учетные данные."
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Проверяем наличие omsId в данных или в настройках клиента
        omsId = data.get('omsId', self.omsid)
        if not omsId:
            error_msg = "Отсутствует идентификатор СУЗ (omsId). Необходимо указать omsId в запросе или в настройках API-клиента."
            logger.error(error_msg)
            # Не прерываем выполнение, возможно API все равно примет запрос
            logger.warning("Продолжаем отправку запроса без omsId")
        
        # Создаем копию данных, чтобы не изменять оригинальные данные
        data_copy = data.copy()
        
        # Удаляем omsId из тела запроса, если он там есть
        if 'omsId' in data_copy:
            del data_copy['omsId']
            logger.info("omsId удален из тела запроса и будет передан в URL-строке")
        
        # URL для отправки данных об использовании КМ с omsId в URL-строке
        url = f"{self.base_url}/api/v2/{self.extension}/utilisation?omsId={omsId}"
        
        # Логируем информацию о запросе
        logger.info(f"Отправка отчета о нанесении. URL: {url}")
        
        # Для заказов используем Content-Type: application/json
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        
        # Проверка обязательных полей для отчета о нанесении
        if "sntins" in data_copy:
            required_fields = ["expirationDate", "seriesNumber", "usageType"]
            missing_fields = [field for field in required_fields if field not in data_copy]
            if missing_fields:
                error_msg = f"Отсутствуют обязательные поля для отчета о нанесении: {', '.join(missing_fields)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Проверка формата даты
            try:
                import datetime
                datetime.datetime.strptime(data_copy["expirationDate"], "%Y-%m-%d")
            except ValueError:
                error_msg = "Поле expirationDate должно быть в формате YYYY-MM-DD"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Проверка допустимых значений типа использования
            allowed_usage_types = ["PRINTED", "VERIFIED"]
            if data_copy["usageType"] not in allowed_usage_types:
                error_msg = f"Недопустимое значение типа использования: {data_copy['usageType']}. Допустимые значения: {', '.join(allowed_usage_types)}"
                logger.error(error_msg)
                # Автоматически исправляем на допустимое значение
                logger.warning(f"Автоматическая замена типа использования на {allowed_usage_types[0]}")
                data_copy["usageType"] = allowed_usage_types[0]
            
            # Логирование дополнительных полей
            logger.info(f"Отчет о нанесении: {len(data_copy['sntins'])} кодов")
            logger.info(f"Срок годности: {data_copy['expirationDate']}")
            logger.info(f"Номер серии: {data_copy['seriesNumber']}")
            logger.info(f"Тип использования: {data_copy['usageType']}")
            
            if data_copy['sntins'] and len(data_copy['sntins']) > 0:
                logger.info(f"Пример кода: {data_copy['sntins'][0]}")
        elif "products" in data_copy:
            logger.info(f"Отчет о нанесении: {len(data_copy['products'])} продуктов")
            for product in data_copy['products']:
                logger.info(f"- GTIN: {product.get('gtin', 'не указан')}, Количество: {product.get('quantity', 0)}")
        
        try:
            # Логируем запрос для отладки
            logger.debug(f"Отправляемые данные: {data_copy}")
            
            # Отправляем запрос с обновленными данными (без omsId в теле) через метод request
            headers['Content-Type'] = 'application/json;charset=UTF-8'
            success, response_data, status_code = self.request(
                method="POST", 
                url=url, 
                data=data_copy, 
                headers=headers, 
                description="Отправка отчета о нанесении кодов маркировки"
            )
            
            # Логируем ответ для отладки
            logger.info(f"Получен ответ от сервера. Статус: {status_code}")
            if response_data:
                logger.info(f"Тело ответа: {response_data}")
                
                # Логирование ошибок валидации полей
                if "fieldErrors" in response_data:
                    for field_error in response_data["fieldErrors"]:
                        logger.error(f"Ошибка валидации поля '{field_error.get('fieldName')}': {field_error.get('fieldError')}")
            
            # Проверяем успешность отправки отчета (особая обработка для отчетов о нанесении)
            # Успешный ответ содержит omsId и reportId, а не поле success
            if ("omsId" in response_data and "reportId" in response_data):
                # Это успешный ответ при отправке отчета о нанесении
                logger.info(f"Отчет о нанесении успешно отправлен. OMS ID: {response_data['omsId']}, Report ID: {response_data['reportId']}")
                # Добавляем флаг success для унификации обработки
                response_data["success"] = True
                return response_data
            
            if status_code >= 400 or not response_data.get("success", False):
                error_message = "Ошибка при отправке отчета о нанесении: "
                if "fieldErrors" in response_data:
                    field_errors = []
                    for field_error in response_data["fieldErrors"]:
                        field_errors.append(f"{field_error.get('fieldName')}: {field_error.get('fieldError')}")
                    error_message += ", ".join(field_errors)
                elif "globalErrors" in response_data:
                    error_message += ", ".join(response_data["globalErrors"])
                elif "error" in response_data:
                    if isinstance(response_data["error"], dict):
                        error_message += response_data["error"].get("message", "Неизвестная ошибка")
                    else:
                        error_message += str(response_data["error"])
                else:
                    error_message += f"Код ответа {status_code}"
                
                logger.warning(error_message)
            else:
                logger.info("Отчет о нанесении успешно отправлен")
            
            return response_data
            
        except requests.RequestException as e:
            error_message = f"Ошибка соединения при отправке отчета о нанесении: {str(e)}"
            logger.error(error_message)
            # Логируем ошибку в БД
            if hasattr(self, 'db') and self.db:
                error_data = {"error": str(e)}
                error_response = type('obj', (object,), {
                    'status_code': 0,
                    'content': b'',
                    'json': lambda: error_data,
                    'request': type('obj', (object,), {'headers': {}})
                })
                self.log_request("POST", url, data_copy, error_response, "Ошибка отправки отчета о нанесении")
            return {"success": False, "error": str(e)}
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заказа на эмиссию кодов маркировки
        
        Формирует и отправляет запрос следующего вида:
        {
            "products": [
                {
                    "gtin": "XXX",
                    "quantity": XXX,
                    "serialNumberType": "XXX",
                    "templateId": XXX
                }
            ],
            "factoryId": "XXX",
            "releaseMethodType": "XXX",
            "factoryCountry": "XXX"
        }
        
        Args:
            order_data (Dict[str, Any]): Данные заказа, которые должны содержать 
                products, factoryId, releaseMethodType, factoryCountry
                
        Returns:
            Dict[str, Any]: Результат создания заказа
            
        Raises:
            ValueError: Если данные заказа не соответствуют требованиям API
            requests.RequestException: Если возникла ошибка при отправке запроса
        """
        # Проверяем наличие токена
        headers = self.get_headers()
        if not headers.get('clientToken'):
            raise ValueError("Отсутствует токен аутентификации (clientToken). Необходимо настроить учетные данные.")
            
        # Проверяем наличие omsId
        if not self.omsid:
            raise ValueError("Отсутствует идентификатор СУЗ (omsId). Необходимо настроить учетные данные.")
        
        # Проверка обязательных полей
        required_fields = ["products", "factoryId", "releaseMethodType", "factoryCountry"]
        for field in required_fields:
            if field not in order_data:
                raise ValueError(f"Отсутствует обязательное поле '{field}'")
        
        # Проверка структуры products
        if not isinstance(order_data.get("products"), list) or not order_data.get("products"):
            raise ValueError("Должна быть хотя бы одна товарная позиция (GTIN)")
        
        # Проверка каждого продукта
        for product in order_data["products"]:
            product_required_fields = ["gtin", "quantity", "serialNumberType", "templateId"]
            for field in product_required_fields:
                if field not in product:
                    raise ValueError(f"Отсутствует обязательное поле '{field}' в описании продукта")
            
            # Проверка GTIN (должен быть строкой из 14 цифр)
            if not isinstance(product["gtin"], str) or not product["gtin"].isdigit() or len(product["gtin"]) != 14:
                raise ValueError("GTIN должен быть строкой из 14 цифр")
            
            # Проверка количества (не более 150000)
            if not isinstance(product["quantity"], int) or product["quantity"] <= 0 or product["quantity"] > 150000:
                raise ValueError("Количество КМ должно быть целым числом от 1 до 150000")
            
            # Проверка типа серийного номера
            valid_serial_types = ["SELF_MADE", "OPERATOR"]
            if product["serialNumberType"] not in valid_serial_types:
                raise ValueError(f"Неверный тип серийного номера. Допустимые значения: {', '.join(valid_serial_types)}")
            
            # Проверка serialNumbers для SELF_MADE
            if product["serialNumberType"] == "SELF_MADE" and "serialNumbers" not in product:
                raise ValueError("Для типа серийного номера SELF_MADE требуется указать массив serialNumbers")
        
        # Проверка releaseMethodType
        valid_release_methods = ["PRODUCTION", "IMPORT", "REMAINS", "CROSSBORDER", "COMMISSION", "DROPSHIPPING", "CONTRACTPRODUCTION", "FOREIGNDISTRIBUTION"]
        if order_data["releaseMethodType"] not in valid_release_methods:
            raise ValueError(f"Неверный тип метода выпуска. Допустимые значения: {', '.join(valid_release_methods)}")
        
        # Для заказов строим URL с обязательным omsId
        url = f"{self.base_url}/api/v2/{self.extension}/orders?omsId={self.omsid}"
        
        # Для заказов используем Content-Type: application/json
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        
        # Логирование заголовков запроса для диагностики
        logger.info(f"Отправка заказа на эмиссию. URL: {url}")
        logger.info(f"Заголовки запроса: {headers}")
        logger.info(f"Данные заказа: {order_data}")
        
        try:
            # Используем метод request вместо прямого вызова session.post
            success, response_data, status_code = self.request(
                method="POST", 
                url=url, 
                data=order_data, 
                headers=headers, 
                description="Создание заказа на эмиссию кодов маркировки"
            )
            
            # Логируем ответ для диагностики
            logger.info(f"Получен ответ от сервера. Статус: {status_code}")
            if response_data:
                logger.info(f"Тело ответа: {response_data}")
            
            # Проверяем наличие ошибок в ответе
            if status_code >= 400 or not response_data.get("success", False):
                error_message = "Ошибка при создании заказа: "
                if "globalErrors" in response_data:
                    error_message += ", ".join(response_data["globalErrors"])
                elif "error" in response_data:
                    if isinstance(response_data["error"], dict):
                        error_message += response_data["error"].get("message", "Неизвестная ошибка")
                    else:
                        error_message += str(response_data["error"])
                else:
                    error_message += f"Код ответа {status_code}"
                
                logger.warning(error_message)
            
            return response_data
            
        except requests.RequestException as e:
            error_message = f"Ошибка соединения при создании заказа: {str(e)}"
            logger.error(error_message)
            self.log_request("POST", url, order_data, None)
            raise

    def get_codes_from_order(self, order_id: str, gtin: str, quantity: int, last_block_id: Optional[str] = None) -> Dict[str, Any]:
        """Получить КМ из заказа
        
        Этот метод позволяет получить массив кодов для заказа. При обращении к этому
        методу исключена возможность перепечатки через интерфейс пользователя.
        
        Args:
            order_id (str): Идентификатор заказа на эмиссию
            gtin (str): GTIN товара, для которого запрашиваются коды
            quantity (int): Количество запрашиваемых кодов (не более 150000)
            last_block_id (str, optional): Идентификатор последнего полученного блока кодов,
                                          используется для пагинации
                                          
        Returns:
            Dict[str, Any]: Результат запроса с кодами маркировки
            
        Raises:
            ValueError: Если параметры запроса не соответствуют требованиям API
            requests.RequestException: Если возникла ошибка при отправке запроса
        """
        # Проверяем наличие токена
        headers = self.get_headers()
        if not headers.get('clientToken'):
            raise ValueError("Отсутствует токен аутентификации (clientToken). Необходимо настроить учетные данные.")
            
        # Проверяем наличие omsId
        if not self.omsid:
            raise ValueError("Отсутствует идентификатор СУЗ (omsId). Необходимо настроить учетные данные.")
        
        # Проверка обязательных параметров
        if not order_id:
            raise ValueError("Отсутствует обязательный параметр 'order_id'")
            
        if not gtin or not isinstance(gtin, str) or not gtin.isdigit() or len(gtin) != 14:
            raise ValueError("GTIN должен быть строкой из 14 цифр")
            
        if not isinstance(quantity, int) or quantity <= 0 or quantity > 150000:
            raise ValueError("Количество КМ должно быть целым числом от 1 до 150000")
        
        # Формируем URL с параметрами согласно шаблону
        url = f"{self.base_url}/api/v2/{self.extension}/codes?omsId={self.omsid}&orderId={order_id}&gtin={gtin}&quantity={quantity}"
        
        # Добавляем lastBlockId если он передан
        if last_block_id:
            url += f"&lastBlockId={last_block_id}"
            
        # Для логирования описание метода
        description = "Получение КМ из заказа"
        
        logger.info(f"Запрос КМ из заказа. URL: {url}")
        
        try:
            # Выполняем GET-запрос напрямую, так как параметры уже в URL
            response = self.session.get(url, headers=headers, timeout=30)
            
            # Логируем запрос
            self.log_request("GET", url, None, response, description)
            
            # Пытаемся получить JSON из ответа
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"content": str(response.content)}
            
            status_code = response.status_code
            
            # Проверяем ответ на успешность
            # Считаем ответ успешным, если код ответа 2xx и есть поле 'codes' в ответе,
            # или если явно указано поле 'success' = True
            if (200 <= status_code < 300 and "codes" in response_data) or response_data.get("success", False):
                # Добавляем флаг success если его нет в ответе
                if "success" not in response_data:
                    response_data["success"] = True
                
                # Проверяем наличие кодов в ответе
                if "codes" in response_data and len(response_data["codes"]) > 0:
                    logger.info(f"Успешно получены коды маркировки ({len(response_data['codes'])})")
                else:
                    logger.warning("Успешный ответ, но коды отсутствуют")
            else:
                # Формируем сообщение об ошибке для логирования
                error_message = "Ошибка при получении КМ из заказа: "
                if "globalErrors" in response_data:
                    error_message += ", ".join(response_data["globalErrors"])
                elif "error" in response_data:
                    if isinstance(response_data["error"], dict):
                        error_message += response_data["error"].get("message", "Неизвестная ошибка")
                    else:
                        error_message += str(response_data["error"])
                else:
                    error_message += f"Код ответа {status_code}"
                
                logger.warning(error_message)
                response_data["success"] = False
            
            # Добавим обновление словаря описаний методов API
            method_key = f"GET:/api/v2/{self.extension}/codes"
            if method_key not in self.method_descriptions:
                self.method_descriptions[method_key] = "Получение КМ из заказа"
            
            return response_data
            
        except requests.RequestException as e:
            error_message = f"Ошибка соединения при получении КМ из заказа: {str(e)}"
            logger.error(error_message)
            raise

    def request(self, method: str, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None, 
                params: Optional[Dict[str, str]] = None, timeout: int = 30, 
                description: Optional[str] = None) -> Tuple[bool, Dict[str, Any], int]:
        """
        Выполняет HTTP запрос к API и логирует результат.
        
        Args:
            method (str): HTTP метод (GET, POST, PUT, DELETE и т.д.)
            url (str): URL для запроса (полный или относительный путь)
            data (Any, optional): Данные для отправки в запросе
            headers (Dict[str, str], optional): Заголовки запроса
            params (Dict[str, str], optional): Параметры URL-запроса
            timeout (int, optional): Таймаут запроса в секундах
            description (str, optional): Описание запроса для логирования
            
        Returns:
            Tuple[bool, Dict[str, Any], int]: Кортеж (успех, данные ответа, код статуса)
        """
        # Формирование полного URL, если передан относительный путь
        if not url.startswith('http'):
            url = f"{self.base_url}{url}"
        
        # Заголовки по умолчанию
        default_headers = self.get_headers()
        
        # Объединение заголовков по умолчанию с переданными заголовками
        if headers:
            request_headers = {**default_headers, **headers}
        else:
            request_headers = default_headers
        
        try:
            # Выполнение запроса
            # Проверяем наличие Content-Type и используем соответствующий параметр для запроса
            is_json = request_headers.get('Content-Type', '').startswith('application/json')
            
            if method.upper() in ['POST', 'PUT', 'PATCH'] and is_json and isinstance(data, str):
                # Если данные уже сериализованы в строку JSON и заголовок соответствует
                response = self.session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
            elif method.upper() in ['POST', 'PUT', 'PATCH'] and is_json and data is not None:
                # Если это JSON запрос, но данные ещё не сериализованы
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,  # Используем json параметр для автоматической сериализации
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
            else:
                # Для всех остальных случаев
                response = self.session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
            
            # Логирование запроса в базу данных
            if self.db:
                self.log_request(method, url, data, response, description)
            
            # Попытка получить данные JSON из ответа
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"content": str(response.content)}
            
            # Определение успешности запроса на основе кода статуса
            success = 200 <= response.status_code < 300
            
            return success, response_data, response.status_code
            
        except requests.RequestException as e:
            # Обработка ошибок запроса
            error_message = str(e)
            error_data = {"error": error_message}
            
            # Логирование ошибки
            logger.error(f"Ошибка API запроса: {error_message}")
            
            # Логирование ошибки в базу данных
            if self.db:
                try:
                    self.log_request(
                        method=method,
                        url=url,
                        data=data,
                        response=None,
                        description=f"{description} (Ошибка: {error_message})" if description else f"Ошибка запроса: {error_message}"
                    )
                except Exception as log_err:
                    logger.error(f"Не удалось залогировать ошибку запроса: {str(log_err)}")
            
            return False, error_data, 0
    
    def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
            description: str = "") -> Tuple[Dict, int]:
        """
        Выполнение GET-запроса
        
        Args:
            url: URL-адрес для запроса
            params: Параметры URL-строки запроса
            headers: Дополнительные заголовки
            description: Описание запроса для логирования
            
        Returns:
            Tuple[Dict, int]: Ответ сервера и код ответа
        """
        success, response_data, status_code = self.request("GET", url, params=params, headers=headers, description=description)
        return response_data, status_code
    
    def post(self, url: str, data: Dict, params: Optional[Dict] = None, 
             headers: Optional[Dict] = None, description: str = "") -> Tuple[Dict, int]:
        """
        Выполнение POST-запроса
        
        Args:
            url: URL-адрес для запроса
            data: Данные для отправки в запросе
            params: Параметры URL-строки запроса
            headers: Дополнительные заголовки
            description: Описание запроса для логирования
            
        Returns:
            Tuple[Dict, int]: Ответ сервера и код ответа
        """
        # Сериализуем данные в JSON перед отправкой
        import json
        json_data = json.dumps(data)
        
        success, response_data, status_code = self.request("POST", url, data=json_data, params=params, headers=headers, description=description)
        return response_data, status_code
    
    def put(self, url: str, data: Dict, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None, description: str = "") -> Tuple[Dict, int]:
        """
        Выполнение PUT-запроса
        
        Args:
            url: URL-адрес для запроса
            data: Данные для отправки в запросе
            params: Параметры URL-строки запроса
            headers: Дополнительные заголовки
            description: Описание запроса для логирования
            
        Returns:
            Tuple[Dict, int]: Ответ сервера и код ответа
        """
        # Проверяем Content-Type и используем json параметр для JSON-данных
        if headers and headers.get('Content-Type', '').startswith('application/json'):
            success, response_data, status_code = self.request("PUT", url, data=data, params=params, headers=headers, description=description)
        else:
            # Обычная отправка данных
            success, response_data, status_code = self.request("PUT", url, data=data, params=params, headers=headers, description=description)
        return response_data, status_code
    
    def delete(self, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None, 
               headers: Optional[Dict] = None, description: str = "") -> Tuple[Dict, int]:
        """
        Выполнение DELETE-запроса
        
        Args:
            url: URL-адрес для запроса
            data: Данные для отправки в запросе
            params: Параметры URL-строки запроса
            headers: Дополнительные заголовки
            description: Описание запроса для логирования
            
        Returns:
            Tuple[Dict, int]: Ответ сервера и код ответа
        """
        # Проверяем Content-Type и используем json параметр для JSON-данных
        if headers and headers.get('Content-Type', '').startswith('application/json') and data:
            success, response_data, status_code = self.request("DELETE", url, data=data, params=params, headers=headers, description=description)
        else:
            # Обычная отправка данных
            success, response_data, status_code = self.request("DELETE", url, data=data, params=params, headers=headers, description=description)
        return response_data, status_code

    def normalize_codes(self, codes: List[str]) -> List[str]:
        """Нормализует коды маркировки, оставляя только часть до первого [GS]
        
        Args:
            codes (List[str]): Список кодов маркировки
            
        Returns:
            List[str]: Список нормализованных кодов
        """
        if not codes:
            return []
            
        normalized_codes = []
        for code in codes:
            if not code:
                continue
                
            # Отладочное логирование для анализа строки
            logger.info(f"Обработка кода: {code}")
            logger.info(f"Длина кода: {len(code)}")
            logger.info(f"Байтовое представление: {code.encode('utf-8')}")
            logger.info(f"Unicode коды символов: {[ord(c) for c in code]}")
            
            # Получаем только часть строки до первого [GS]
            # Вариант с символьным представлением [GS]
            if '[GS]' in code:
                normalized_code = code.split('[GS]')[0]
                logger.info(f"Найден [GS] в текстовом виде")
            # Вариант с Unicode символом GS (Group Separator)
            elif '\u001d' in code:
                normalized_code = code.split('\u001d')[0]
                logger.info(f"Найден \u001d (Unicode GS)")
            # Вариант с другим представлением GS в Unicode
            elif '\x1d' in code:
                normalized_code = code.split('\x1d')[0]
                logger.info(f"Найден \x1d (hex GS)")
            # Проверяем все возможные представления GS в Unicode
            else:
                # Преобразуем строку в байты для поиска всех возможных представлений GS
                code_bytes = code.encode('utf-8')
                gs_positions = []
                
                # Ищем все возможные представления GS
                for i in range(len(code_bytes)):
                    if code_bytes[i] == 0x1d:  # GS в hex
                        gs_positions.append(i)
                        logger.info(f"Найден GS в позиции {i} (байт {code_bytes[i]})")
                
                if gs_positions:
                    # Берем позицию первого GS
                    first_gs_pos = gs_positions[0]
                    # Преобразуем обратно в строку до первого GS
                    normalized_code = code_bytes[:first_gs_pos].decode('utf-8')
                    logger.info(f"Нормализован код маркировки: оставлена часть до GS символа (bytes)")
                else:
                    normalized_code = code
                    logger.info("GS символ не найден в коде")
                
            logger.info(f"Нормализованный код: {normalized_code}")
            normalized_codes.append(normalized_code)
            
        return normalized_codes