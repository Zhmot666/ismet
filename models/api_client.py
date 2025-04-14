import requests
import json
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

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
            "POST:/api/v2/pharma/utilisation": "Отправка данных об использовании КМ",
            
            # Молочная продукция
            "GET:/api/v2/milk/ping": "Проверка доступности СУЗ (молочная продукция)",
            "GET:/api/v2/milk/version": "Получение версии СУЗ и API (молочная продукция)",
            "GET:/api/v2/milk/orders": "Получение списка заказов (молочная продукция)",
            "GET:/api/v2/milk/codes": "Получение списка кодов маркировки (молочная продукция)",
            "GET:/api/v2/milk/aggregation": "Получение данных агрегации (молочная продукция)",
            "GET:/api/v2/milk/report": "Получение отчета СУЗ (молочная продукция)",
            "POST:/api/v2/milk/orders": "Отправка заказа на эмиссию КМ (молочная продукция)",
            "POST:/api/v2/milk/aggregation": "Отправка данных агрегации (молочная продукция)",
            "POST:/api/v2/milk/utilisation": "Отправка данных об использовании КМ (молочная продукция)",
            
            # Табачная продукция
            "GET:/api/v2/tobacco/ping": "Проверка доступности СУЗ (табачная продукция)",
            "GET:/api/v2/tobacco/version": "Получение версии СУЗ и API (табачная продукция)",
            "GET:/api/v2/tobacco/orders": "Получение списка заказов (табачная продукция)",
            "GET:/api/v2/tobacco/codes": "Получение списка кодов маркировки (табачная продукция)",
            "GET:/api/v2/tobacco/aggregation": "Получение данных агрегации (табачная продукция)",
            "GET:/api/v2/tobacco/report": "Получение отчета СУЗ (табачная продукция)",
            "POST:/api/v2/tobacco/orders": "Отправка заказа на эмиссию КМ (табачная продукция)",
            "POST:/api/v2/tobacco/aggregation": "Отправка данных агрегации (табачная продукция)",
            "POST:/api/v2/tobacco/utilisation": "Отправка данных об использовании КМ (табачная продукция)",
            
            # Обувные товары
            "GET:/api/v2/shoes/ping": "Проверка доступности СУЗ (обувь)",
            "GET:/api/v2/shoes/version": "Получение версии СУЗ и API (обувь)",
            "GET:/api/v2/shoes/orders": "Получение списка заказов (обувь)",
            "GET:/api/v2/shoes/codes": "Получение списка кодов маркировки (обувь)",
            "GET:/api/v2/shoes/aggregation": "Получение данных агрегации (обувь)",
            "GET:/api/v2/shoes/report": "Получение отчета СУЗ (обувь)",
            "POST:/api/v2/shoes/orders": "Отправка заказа на эмиссию КМ (обувь)",
            "POST:/api/v2/shoes/aggregation": "Отправка данных агрегации (обувь)",
            "POST:/api/v2/shoes/utilisation": "Отправка данных об использовании КМ (обувь)",
            
            # Алкогольная продукция
            "GET:/api/v2/alcohol/ping": "Проверка доступности СУЗ (алкоголь)",
            "GET:/api/v2/alcohol/version": "Получение версии СУЗ и API (алкоголь)",
            "GET:/api/v2/alcohol/orders": "Получение списка заказов (алкоголь)",
            "GET:/api/v2/alcohol/codes": "Получение списка кодов маркировки (алкоголь)",
            "GET:/api/v2/alcohol/aggregation": "Получение данных агрегации (алкоголь)",
            "GET:/api/v2/alcohol/report": "Получение отчета СУЗ (алкоголь)",
            "POST:/api/v2/alcohol/orders": "Отправка заказа на эмиссию КМ (алкоголь)",
            "POST:/api/v2/alcohol/aggregation": "Отправка данных агрегации (алкоголь)",
            "POST:/api/v2/alcohol/utilisation": "Отправка данных об использовании КМ (алкоголь)",
            
            # Товары легкой промышленности
            "GET:/api/v2/lp/ping": "Проверка доступности СУЗ (легпром)",
            "GET:/api/v2/lp/version": "Получение версии СУЗ и API (легпром)",
            "GET:/api/v2/lp/orders": "Получение списка заказов (легпром)",
            "GET:/api/v2/lp/codes": "Получение списка кодов маркировки (легпром)",
            "GET:/api/v2/lp/aggregation": "Получение данных агрегации (легпром)",
            "GET:/api/v2/lp/report": "Получение отчета СУЗ (легпром)",
            "POST:/api/v2/lp/orders": "Отправка заказа на эмиссию КМ (легпром)",
            "POST:/api/v2/lp/aggregation": "Отправка данных агрегации (легпром)",
            "POST:/api/v2/lp/utilisation": "Отправка данных об использовании КМ (легпром)",
            
            # Питьевая вода
            "GET:/api/v2/water/ping": "Проверка доступности СУЗ (вода)",
            "GET:/api/v2/water/version": "Получение версии СУЗ и API (вода)",
            "GET:/api/v2/water/orders": "Получение списка заказов (вода)",
            "GET:/api/v2/water/codes": "Получение списка кодов маркировки (вода)",
            "GET:/api/v2/water/aggregation": "Получение данных агрегации (вода)",
            "GET:/api/v2/water/report": "Получение отчета СУЗ (вода)",
            "POST:/api/v2/water/orders": "Отправка заказа на эмиссию КМ (вода)",
            "POST:/api/v2/water/aggregation": "Отправка данных агрегации (вода)",
            "POST:/api/v2/water/utilisation": "Отправка данных об использовании КМ (вода)",
            
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
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
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
                
                request_str = json.dumps(request_data)
                response_str = json.dumps(response.json()) if response.content else "{}"
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
    
    def post_aggregation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка агрегации"""
        url = f"{self.base_url}/api/v2/{self.extension}/aggregation"
        headers = self.get_headers()
        response = self.session.post(url, json=data, headers=headers)
        self.log_request("POST", url, data, response)
        return response.json()
    
    def post_utilisation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка данных об использовании"""
        url = f"{self.base_url}/api/v2/{self.extension}/utilisation"
        headers = self.get_headers()
        response = self.session.post(url, json=data, headers=headers)
        self.log_request("POST", url, data, response)
        return response.json()
    
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
        
        # Формируем тело запроса для создания заказа
        request_body = {
            "products": order_data["products"],
            "factoryId": order_data["factoryId"],
            "releaseMethodType": order_data["releaseMethodType"],
            "factoryCountry": order_data["factoryCountry"]
        }
        
        # Логирование заголовков запроса для диагностики
        logger.info(f"Отправка заказа на эмиссию. URL: {url}")
        logger.info(f"Заголовки запроса: {headers}")
        logger.info(f"Данные заказа: {request_body}")
        
        try:
            response = self.session.post(url, json=request_body, headers=headers)
            
            # Логируем ответ для диагностики
            logger.info(f"Получен ответ от сервера. Статус: {response.status_code}")
            if response.content:
                try:
                    logger.info(f"Тело ответа: {response.json()}")
                except Exception:
                    logger.info(f"Тело ответа не является JSON: {response.text[:200]}")
            
            # Логируем запрос в БД
            self.log_request("POST", url, request_body, response)
            
            # Проверяем наличие ошибок в ответе
            json_response = response.json()
            if not response.ok or not json_response.get("success", False):
                error_message = "Ошибка при создании заказа: "
                if "globalErrors" in json_response:
                    error_message += ", ".join(json_response["globalErrors"])
                elif "error" in json_response:
                    if isinstance(json_response["error"], dict):
                        error_message += json_response["error"].get("message", "Неизвестная ошибка")
                    else:
                        error_message += str(json_response["error"])
                else:
                    error_message += f"Код ответа {response.status_code}"
                
                logger.warning(error_message)
            
            return json_response
            
        except requests.RequestException as e:
            error_message = f"Ошибка соединения при создании заказа: {str(e)}"
            logger.error(error_message)
            self.log_request("POST", url, request_body, None)
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
        
        # Формируем параметры запроса
        params = {
            "omsId": self.omsid,
            "orderId": order_id,
            "gtin": gtin,
            "quantity": str(quantity)
        }
        
        # Добавляем lastBlockId если он передан
        if last_block_id:
            params["lastBlockId"] = last_block_id
            
        # Строим URL для запроса
        url = f"{self.base_url}/api/v2/{self.extension}/codes"
        
        # Для логирования описание метода
        description = "Получение КМ из заказа"
        
        logger.info(f"Запрос КМ из заказа. URL: {url}, Параметры: {params}")
        
        try:
            # Используем метод get для выполнения запроса
            response_data, status_code = self.get(
                url=url, 
                params=params,
                headers=headers,
                description=description
            )
            
            # Проверяем наличие ошибок в ответе
            if status_code >= 400 or not response_data.get("success", False):
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
            
            # Логирование запроса через api_logger, если он доступен
            if self.api_logger:
                # Преобразование request_data и response_data в формат JSON, если это возможно
                request_data = data
                try:
                    response_data = response.json() if response.content else {}
                except ValueError:
                    response_data = {"raw_content": str(response.content)}
                
                # Логирование через APILog
                self.api_logger.log_request(
                    method=method,
                    url=url,
                    request_data=json.dumps(request_data) if request_data else "{}",
                    response_data=json.dumps(response_data) if response_data else "{}",
                    status_code=response.status_code,
                    success=200 <= response.status_code < 300,
                    description=description
                )
            
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
            
            # Логирование через api_logger при ошибке
            if self.api_logger:
                self.api_logger.log_request(
                    method=method,
                    url=url,
                    request_data=json.dumps(data) if data else "{}",
                    response_data=json.dumps(error_data),
                    status_code=0,  # Код 0 для ошибок подключения
                    success=False,
                    description=f"{description} (Ошибка: {error_message})" if description else f"Ошибка запроса: {error_message}"
                )
            
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
        return self.request("GET", url, params=params, headers=headers, description=description)
    
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
        return self.request("POST", url, data=data, params=params, headers=headers, description=description)
    
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
        return self.request("PUT", url, data=data, params=params, headers=headers, description=description)
    
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
        return self.request("DELETE", url, data=data, params=params, headers=headers, description=description) 