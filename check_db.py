import sqlite3
import sys

def check_database(db_path):
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        conn.text_factory = str  # Чтобы правильно обрабатывать русские символы
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"- {table[0]}")
        
        # Проверяем наличие таблицы order_statuses
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_statuses'")
        if cursor.fetchone():
            print("\nТаблица order_statuses существует")
            
            # Получаем структуру таблицы
            cursor.execute("PRAGMA table_info(order_statuses)")
            columns = cursor.fetchall()
            print(f"Столбцы таблицы order_statuses:")
            for column in columns:
                print(f"- {column[1]} ({column[2]})")
            
            # Получаем данные из таблицы
            cursor.execute("SELECT * FROM order_statuses")
            rows = cursor.fetchall()
            print(f"\nЗаписей в таблице order_statuses: {len(rows)}")
            for row in rows:
                print(f"- {row}")
            
            # Проверяем наличие всех стандартных статусов заказов
            standard_statuses = ["CREATED", "PENDING", "DECLINED", "APPROVED", "READY", "CLOSED"]
            cursor.execute("SELECT code FROM order_statuses")
            existing_codes = [row[0] for row in cursor.fetchall()]
            
            missing_statuses = [status for status in standard_statuses if status not in existing_codes]
            if missing_statuses:
                print(f"\nОтсутствуют стандартные статусы: {', '.join(missing_statuses)}")
                
                # Спрашиваем, хочет ли пользователь восстановить отсутствующие статусы
                choice = input("Восстановить отсутствующие статусы? (y/n): ")
                if choice.lower() == 'y':
                    # Добавляем отсутствующие статусы
                    default_statuses = {
                        "CREATED": ("Заказ создан", "Заказ создан в системе"),
                        "PENDING": ("Заказ ожидает подтверждения", "Заказ ожидает подтверждения в системе маркировки"),
                        "DECLINED": ("Заказ не подтверждён", "Заказ не подтверждён в системе маркировки"),
                        "APPROVED": ("Заказ подтверждён", "Заказ подтверждён в системе маркировки"),
                        "READY": ("Заказ готов", "Заказ готов к использованию"),
                        "CLOSED": ("Заказ закрыт", "Заказ закрыт (обработан)")
                    }
                    
                    for code in missing_statuses:
                        name, description = default_statuses[code]
                        cursor.execute(
                            "INSERT INTO order_statuses (code, name, description) VALUES (?, ?, ?)",
                            (code, name, description)
                        )
                        print(f"Восстановлен статус: {code} - {name}")
                    
                    conn.commit()
                    print("Изменения сохранены в базе данных")
                    
                    # Показываем обновленную таблицу
                    cursor.execute("SELECT * FROM order_statuses")
                    rows = cursor.fetchall()
                    print(f"\nЗаписей в таблице order_statuses после восстановления: {len(rows)}")
                    for row in rows:
                        print(f"- {row}")
            else:
                print("\nВсе стандартные статусы заказов присутствуют в базе данных")
        else:
            print("\nТаблица order_statuses НЕ существует!")
        
        conn.close()
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {str(e)}")

if __name__ == "__main__":
    # Настройка для правильного отображения кириллицы в Windows
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)

    db_path = "database.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Проверка базы данных: {db_path}")
    check_database(db_path) 