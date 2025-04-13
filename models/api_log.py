import json
import datetime
from typing import Dict, Any, Optional, List, Tuple

class APILog:
    """Класс для управления логами API-запросов"""
    
    def __init__(self, db=None):
        """
        Инициализация объекта для логирования API-запросов
        
        Args:
            db: Объект базы данных для сохранения логов
        """
        self.db = db
    
    def log_request(self, method: str, url: str, request_data: Any, 
                   response_data: Any, status_code: int, 
                   success: bool, description: Optional[str] = None) -> int:
        """
        Логирование API-запроса в базу данных
        
        Args:
            method: HTTP-метод (GET, POST и т.д.)
            url: URL запроса
            request_data: Данные запроса
            response_data: Данные ответа
            status_code: Код статуса ответа
            success: Флаг успешности запроса
            description: Описание запроса
            
        Returns:
            int: ID записи в базе данных или -1 при ошибке
        """
        if self.db is None:
            print("База данных не инициализирована для логирования")
            return -1
        
        try:
            # Преобразуем данные в строки JSON
            request_str = json.dumps(request_data) if request_data else "{}"
            response_str = json.dumps(response_data) if response_data else "{}"
            
            # Добавляем запись в базу данных
            log_id = self.db.add_api_log(
                method=method,
                url=url,
                request=request_str,
                response=response_str,
                status_code=status_code,
                success=success,
                description=description
            )
            
            return log_id
            
        except Exception as e:
            print(f"Ошибка при логировании запроса: {str(e)}")
            return -1
    
    def get_logs(self, limit: int = 100, 
                offset: int = 0, 
                success: Optional[bool] = None, 
                method: Optional[str] = None,
                url_pattern: Optional[str] = None,
                date_from: Optional[datetime.datetime] = None,
                date_to: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение списка логов API-запросов с возможностью фильтрации
        
        Args:
            limit: Максимальное количество записей
            offset: Смещение выборки
            success: Фильтр по успешности запроса
            method: Фильтр по HTTP-методу
            url_pattern: Шаблон для поиска в URL
            date_from: Начальная дата для фильтрации
            date_to: Конечная дата для фильтрации
            
        Returns:
            List[Dict[str, Any]]: Список записей логов
        """
        if self.db is None:
            print("База данных не инициализирована для получения логов")
            return []
        
        try:
            return self.db.get_api_logs(
                limit=limit,
                offset=offset,
                success=success,
                method=method,
                url_pattern=url_pattern,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            print(f"Ошибка при получении логов API-запросов: {str(e)}")
            return []
    
    def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение записи лога API-запроса по ID
        
        Args:
            log_id: ID записи в базе данных
            
        Returns:
            Optional[Dict[str, Any]]: Запись лога или None при ошибке
        """
        if self.db is None:
            print("База данных не инициализирована для получения лога")
            return None
        
        try:
            return self.db.get_api_log_by_id(log_id)
        except Exception as e:
            print(f"Ошибка при получении лога API-запроса по ID: {str(e)}")
            return None
    
    def get_stats(self, period: str = 'day') -> Dict[str, Any]:
        """
        Получение статистики по API-запросам
        
        Args:
            period: Период статистики ('day', 'week', 'month', 'year')
            
        Returns:
            Dict[str, Any]: Статистика API-запросов
        """
        if self.db is None:
            print("База данных не инициализирована для получения статистики")
            return {}
        
        try:
            # Определяем дату начала периода
            now = datetime.datetime.now()
            if period == 'day':
                date_from = now - datetime.timedelta(days=1)
            elif period == 'week':
                date_from = now - datetime.timedelta(weeks=1)
            elif period == 'month':
                date_from = now - datetime.timedelta(days=30)
            elif period == 'year':
                date_from = now - datetime.timedelta(days=365)
            else:
                date_from = now - datetime.timedelta(days=1)  # По умолчанию - день
            
            # Получаем базовую статистику
            total_requests = self.db.count_api_logs(date_from=date_from)
            successful_requests = self.db.count_api_logs(date_from=date_from, success=True)
            failed_requests = self.db.count_api_logs(date_from=date_from, success=False)
            
            # Получаем статистику по методам
            method_stats = self.db.get_method_stats(date_from=date_from)
            
            # Получаем статистику по URL
            url_stats = self.db.get_url_stats(date_from=date_from)
            
            # Формируем и возвращаем результат
            return {
                'period': period,
                'date_from': date_from.isoformat(),
                'date_to': now.isoformat(),
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'method_stats': method_stats,
                'url_stats': url_stats
            }
            
        except Exception as e:
            print(f"Ошибка при получении статистики API-запросов: {str(e)}")
            return {}
    
    def delete_logs(self, log_ids: List[int] = None, 
                   before_date: Optional[datetime.datetime] = None) -> int:
        """
        Удаление логов API-запросов
        
        Args:
            log_ids: Список ID записей для удаления
            before_date: Удаление всех записей до указанной даты
            
        Returns:
            int: Количество удаленных записей
        """
        if self.db is None:
            print("База данных не инициализирована для удаления логов")
            return 0
        
        try:
            if log_ids:
                return self.db.delete_api_logs_by_ids(log_ids)
            elif before_date:
                return self.db.delete_api_logs_before_date(before_date)
            else:
                print("Не указаны параметры для удаления логов")
                return 0
        except Exception as e:
            print(f"Ошибка при удалении логов API-запросов: {str(e)}")
            return 0
    
    def export_logs(self, filename: str, 
                   format_type: str = 'json',
                   log_ids: List[int] = None,
                   date_from: Optional[datetime.datetime] = None,
                   date_to: Optional[datetime.datetime] = None) -> bool:
        """
        Экспорт логов API-запросов в файл
        
        Args:
            filename: Имя файла для экспорта
            format_type: Формат экспорта ('json' или 'csv')
            log_ids: Список ID записей для экспорта
            date_from: Начальная дата для фильтрации
            date_to: Конечная дата для фильтрации
            
        Returns:
            bool: True, если экспорт успешен, иначе False
        """
        if self.db is None:
            print("База данных не инициализирована для экспорта логов")
            return False
        
        try:
            # Получаем логи по фильтрам
            logs = []
            if log_ids:
                for log_id in log_ids:
                    log = self.db.get_api_log_by_id(log_id)
                    if log:
                        logs.append(log)
            else:
                logs = self.db.get_api_logs(
                    limit=10000,  # Большое значение для экспорта
                    offset=0,
                    date_from=date_from,
                    date_to=date_to
                )
            
            if not logs:
                print("Нет логов для экспорта")
                return False
            
            # Экспортируем в выбранном формате
            if format_type.lower() == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=4, default=str)
                return True
            elif format_type.lower() == 'csv':
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'timestamp', 'method', 'url', 'request', 
                                 'response', 'status_code', 'success', 'description']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for log in logs:
                        # Преобразуем request и response в строки для CSV
                        log_copy = log.copy()
                        if isinstance(log_copy.get('request'), dict):
                            log_copy['request'] = json.dumps(log_copy['request'])
                        if isinstance(log_copy.get('response'), dict):
                            log_copy['response'] = json.dumps(log_copy['response'])
                        writer.writerow(log_copy)
                return True
            else:
                print(f"Неподдерживаемый формат экспорта: {format_type}")
                return False
            
        except Exception as e:
            print(f"Ошибка при экспорте логов API-запросов: {str(e)}")
            return False 