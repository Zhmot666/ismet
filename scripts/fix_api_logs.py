#!/usr/bin/env python
"""
Скрипт для исправления формата данных в таблице api_logs.
Позволяет преобразовать нестандартные форматы данных request и response в JSON строки.
"""
import os
import sys
import json
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_database_path():
    """Поиск пути к базе данных"""
    # Путь относительно текущего скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # Возможные пути к базе данных
    possible_paths = [
        os.path.join(root_dir, 'database.db'),
        os.path.join(root_dir, 'data', 'database.db'),
        os.path.join(os.path.expanduser('~'), '.ismet', 'database.db')
    ]
    
    # Проверяем каждый путь
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Найдена база данных: {path}")
            return path
    
    # Если не найдено, спрашиваем пользователя
    print("База данных не найдена в стандартных путях.")
    custom_path = input("Введите путь к базе данных: ")
    if os.path.exists(custom_path):
        return custom_path
    else:
        logger.error(f"База данных не найдена по пути: {custom_path}")
        return None

def fix_api_logs(db_path):
    """Исправление записей в таблице api_logs"""
    if not db_path:
        logger.error("Путь к базе данных не указан")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Проверяем наличие таблицы api_logs
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_logs'")
        if not cursor.fetchone():
            logger.error("Таблица api_logs не найдена в базе данных")
            return
        
        # Получаем все записи из таблицы api_logs
        cursor.execute("SELECT id, request, response FROM api_logs")
        logs = cursor.fetchall()
        
        logger.info(f"Найдено {len(logs)} записей для обработки")
        
        # Счетчики для статистики
        fixed_count = 0
        error_count = 0
        
        # Обрабатываем каждую запись
        for log in logs:
            log_id = log['id']
            request_data = log['request']
            response_data = log['response']
            
            try:
                # Проверяем и исправляем request
                if request_data:
                    # Пробуем парсить JSON для проверки
                    try:
                        # Если это уже валидный JSON, пропускаем
                        json.loads(request_data)
                    except (json.JSONDecodeError, TypeError):
                        # Если это не JSON, преобразуем в JSON строку
                        request_json = json.dumps({"data": str(request_data)})
                        cursor.execute(
                            "UPDATE api_logs SET request = ? WHERE id = ?",
                            (request_json, log_id)
                        )
                        logger.debug(f"Исправлен request для записи {log_id}")
                else:
                    # Если пусто, устанавливаем пустой объект JSON
                    cursor.execute(
                        "UPDATE api_logs SET request = ? WHERE id = ?",
                        ("{}", log_id)
                    )
                    logger.debug(f"Установлен пустой JSON для request записи {log_id}")
                
                # Проверяем и исправляем response
                if response_data:
                    # Пробуем парсить JSON для проверки
                    try:
                        # Если это уже валидный JSON, пропускаем
                        json.loads(response_data)
                    except (json.JSONDecodeError, TypeError):
                        # Если это не JSON, преобразуем в JSON строку
                        response_json = json.dumps({"data": str(response_data)})
                        cursor.execute(
                            "UPDATE api_logs SET response = ? WHERE id = ?",
                            (response_json, log_id)
                        )
                        logger.debug(f"Исправлен response для записи {log_id}")
                else:
                    # Если пусто, устанавливаем пустой объект JSON
                    cursor.execute(
                        "UPDATE api_logs SET response = ? WHERE id = ?",
                        ("{}", log_id)
                    )
                    logger.debug(f"Установлен пустой JSON для response записи {log_id}")
                
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка при обработке записи {log_id}: {str(e)}")
                error_count += 1
        
        # Сохраняем изменения
        conn.commit()
        
        logger.info(f"Обработка завершена. Исправлено записей: {fixed_count}, ошибок: {error_count}")
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite: {str(e)}")
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Точка входа в скрипт"""
    logger.info("Запуск скрипта исправления таблицы api_logs")
    
    # Находим путь к базе данных
    db_path = find_database_path()
    if not db_path:
        logger.error("База данных не найдена. Завершение работы.")
        return
    
    # Исправляем записи
    fix_api_logs(db_path)
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    main() 