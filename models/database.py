import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
import time
import logging
import json

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, Session, relationship
from sqlalchemy.ext.declarative import declarative_base

from models.models import Order, Connection, Credentials, Nomenclature, Extension, EmissionType, Country, OrderStatus, APIOrder
import os
import time

# Инициализация логгера
logger = logging.getLogger(__name__)

Base = declarative_base()

class UserORM:
    """ORM класс для работы с пользователями"""
    table_name = "users"
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """


class APIOrderORM:
    """ORM класс для работы с API заказами"""
    table_name = "api_orders"
    create_table_query = """
    CREATE TABLE IF NOT EXISTS api_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL UNIQUE,
        order_status TEXT NOT NULL,
        order_status_description TEXT,
        created_timestamp TEXT NOT NULL,
        total_quantity INTEGER NOT NULL,
        num_of_products INTEGER NOT NULL,
        product_group_type TEXT NOT NULL,
        signed BOOLEAN NOT NULL,
        verified BOOLEAN NOT NULL,
        buffers TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """


class OrderORM(Base):
    """Модель заказа в SQLAlchemy"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String, nullable=False)
    timestamp = Column(String)
    expected_complete = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class OrderProductORM(Base):
    """Модель деталей заказа (товаров) в SQLAlchemy"""
    __tablename__ = 'order_products'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    gtin = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    order = relationship("OrderORM")

class AggregationORM(Base):
    """Модель агрегации в SQLAlchemy"""
    __tablename__ = 'aggregations'
    
    id = Column(Integer, primary_key=True)
    code = Column(String)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class ConnectionORM(Base):
    """Модель подключения в SQLAlchemy"""
    __tablename__ = 'connections'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Integer, default=0)  # 0 - неактивно, 1 - активно
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CredentialsORM(Base):
    """Модель учетных данных в SQLAlchemy"""
    __tablename__ = 'credentials'
    
    id = Column(Integer, primary_key=True)
    omsid = Column(String, nullable=False)
    token = Column(String, nullable=False)
    gln = Column(String, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class NomenclatureORM(Base):
    """Модель номенклатуры в SQLAlchemy"""
    __tablename__ = 'nomenclature'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    gtin = Column(String, nullable=False)
    product_group = Column(String, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ExtensionORM(Base):
    """Модель расширения API в SQLAlchemy"""
    __tablename__ = 'extensions'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Integer, default=0)  # 0 - неактивно, 1 - активно
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class EmissionTypeORM(Base):
    """Модель типа эмиссии (способа выпуска товара) в SQLAlchemy"""
    __tablename__ = 'emission_types'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    product_group = Column(String)  # Для каких товарных групп доступен (None - для всех)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CountryORM(Base):
    """Модель страны мира в SQLAlchemy"""
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class OrderStatusORM(Base):
    """Модель статуса заказа в SQLAlchemy"""
    __tablename__ = 'order_statuses'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Database:
    """Класс для работы с базой данных"""
    def __init__(self, db_path: str = "database.db"):
        """Инициализация подключения к базе данных"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Создание таблиц, если они не существуют
        cursor = self.conn.cursor()
        
        # Создание таблицы для пользователей
        cursor.execute(UserORM.create_table_query)
        
        # Создание таблицы для API заказов
        cursor.execute(APIOrderORM.create_table_query)
        
        self.create_tables()
        self.migrate_database()
        self.migrate_api_order_structure()  # Миграция структуры API заказов
        self.insert_default_extensions()
        self.insert_default_emission_types()
        self.insert_default_countries()
        self.insert_default_order_statuses()
    
    def create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.conn.cursor()
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL,
                timestamp TEXT,
                expected_complete TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица деталей заказа (товаров)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                gtin TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Таблица подключений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                is_active INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица учетных данных
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                omsid TEXT NOT NULL,
                token TEXT NOT NULL,
                gln TEXT DEFAULT ''
            )
        ''')
        
        # Таблица номенклатуры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nomenclature (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gtin TEXT NOT NULL,
                product_group TEXT DEFAULT ""
            )
        ''')
        
        # Таблица расширений API (категорий продукции)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extensions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица типов эмиссии (способов выпуска товара)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emission_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                product_group TEXT
            )
        ''')
        
        # Таблица стран мира
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица статусов заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL
            )
        ''')
        
        # Таблица логов API
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
        
        self.conn.commit()
        logger.info("Таблицы в базе данных созданы")
    
    def migrate_database(self):
        """Миграция базы данных - добавление новых полей в существующие таблицы"""
        cursor = self.conn.cursor()
        
        # Проверяем и добавляем столбец product_group в таблицу nomenclature
        cursor.execute("PRAGMA table_info(nomenclature)")
        columns = cursor.fetchall()
        column_names = [column["name"] for column in columns]
        
        # Если колонки нет, добавляем её
        if "product_group" not in column_names:
            try:
                cursor.execute("ALTER TABLE nomenclature ADD COLUMN product_group TEXT DEFAULT ''")
                self.conn.commit()
                logger.info("Добавлена колонка product_group в таблицу nomenclature")
            except Exception as e:
                logger.error(f"Ошибка при миграции базы данных: {str(e)}")
        
        # Проверяем и добавляем столбец gln в таблицу credentials
        cursor.execute("PRAGMA table_info(credentials)")
        columns = cursor.fetchall()
        column_names = [column["name"] for column in columns]
        
        # Если колонки нет, добавляем её
        if "gln" not in column_names:
            try:
                cursor.execute("ALTER TABLE credentials ADD COLUMN gln TEXT DEFAULT ''")
                self.conn.commit()
                logger.info("Добавлена колонка gln в таблицу credentials")
            except Exception as e:
                logger.error(f"Ошибка при миграции базы данных: {str(e)}")
                
        # Проверяем и добавляем столбец timestamp в таблицу orders
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()
        column_names = [column["name"] for column in columns]
        
        # Если колонки нет, добавляем её
        if "timestamp" not in column_names:
            try:
                cursor.execute("ALTER TABLE orders ADD COLUMN timestamp TEXT")
                self.conn.commit()
                logger.info("Добавлена колонка timestamp в таблицу orders")
            except Exception as e:
                logger.error(f"Ошибка при миграции базы данных: {str(e)}")
        
        # Проверяем и добавляем столбец expected_complete в таблицу orders
        if "expected_complete" not in column_names:
            try:
                cursor.execute("ALTER TABLE orders ADD COLUMN expected_complete TEXT")
                self.conn.commit()
                logger.info("Добавлена колонка expected_complete в таблицу orders")
            except Exception as e:
                logger.error(f"Ошибка при миграции базы данных: {str(e)}")
        else:
            # Проверяем тип колонки expected_complete и при необходимости мигрируем данные
            try:
                # Проверяем, есть ли записи с числовыми значениями
                cursor.execute("SELECT id, expected_complete FROM orders WHERE expected_complete IS NOT NULL AND expected_complete != ''")
                rows = cursor.fetchall()
                
                for row in rows:
                    order_id = row[0]
                    expected_complete_value = row[1]
                    
                    # Проверяем, является ли значение числом
                    try:
                        minutes = int(expected_complete_value)
                        # Если это число минут, преобразуем в строку даты
                        # Предполагаем, что это минуты с момента создания заказа
                        cursor.execute("SELECT created_at FROM orders WHERE id = ?", (order_id,))
                        created_at_row = cursor.fetchone()
                        
                        if created_at_row:
                            try:
                                created_at = datetime.strptime(created_at_row[0], "%Y-%m-%d %H:%M:%S")
                                # Добавляем указанное количество минут
                                expected_time = created_at.timestamp() + (minutes * 60)
                                expected_date = datetime.fromtimestamp(expected_time)
                                formatted_date = expected_date.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # Обновляем значение в базе данных
                                cursor.execute("UPDATE orders SET expected_complete = ? WHERE id = ?", 
                                              (formatted_date, order_id))
                                logger.info(f"Мигрирован формат даты для заказа {order_id}")
                            except Exception as e:
                                logger.error(f"Ошибка при преобразовании даты для заказа {order_id}: {str(e)}")
                    except ValueError:
                        # Если это не число, ничего не делаем
                        pass
                
                self.conn.commit()
                logger.info("Миграция данных expected_complete завершена")
            except Exception as e:
                logger.error(f"Ошибка при миграции данных expected_complete: {str(e)}")
        
        # Проверяем существование таблицы статусов заказов
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_statuses'")
        if not cursor.fetchone():
            # Если таблицы нет, создаем её
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_statuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT
                )
            ''')
    
    def insert_default_extensions(self):
        """Вставка значений расширений по умолчанию, если таблица пуста"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM extensions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            extensions = [
                ("shoes", "Обувные товары"),
                ("tobacco", "Табачной изделия"),
                ("alcohol", "Алкоголь"),
                ("pharma", "Фармацевтика"),
                ("milk", "Молочная продукция"),
                ("lp", "Товары легкой промышленности"),
                ("water", "Питевая вода")
            ]
            
            # Сделаем pharma активным по умолчанию
            for code, name in extensions:
                is_active = 1 if code == "pharma" else 0
                cursor.execute(
                    "INSERT INTO extensions (code, name, is_active) VALUES (?, ?, ?)",
                    (code, name, is_active)
                )
            
            self.conn.commit()
            logger.info("Значения расширений API по умолчанию добавлены")
    
    def insert_default_emission_types(self):
        """Вставка значений типов эмиссии по умолчанию, если таблица пуста"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emission_types")
        count = cursor.fetchone()[0]
        
        if count == 0:
            emission_types = [
                ("PRODUCTION", "Производство в Казахстане", None),
                ("IMPORT", "Ввезен в Казахстан (Импорт)", None),
                ("REMAINS", "Маркировка остатков", "shoes"),
                ("COMMISSION", "Принят на коммиссию от физ.лица", "shoes"),
                ("REMARK", "Перемаркировка", None)
            ]
            
            for code, name, product_group in emission_types:
                cursor.execute("""
                    INSERT INTO emission_types (code, name, product_group)
                    VALUES (?, ?, ?)
                """, (code, name, product_group))
            
            self.conn.commit()
            logger.info("Значения типов эмиссии по умолчанию добавлены")
    
    def insert_default_countries(self):
        """Вставка значений стран мира по умолчанию, если таблица пуста"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM countries")
        count = cursor.fetchone()[0]
        
        if count == 0:
            countries = [
                ("AU", "АВСТРАЛИЯ"),
                ("AT", "АВСТРИЯ"),
                ("AZ", "АЗЕРБАЙДЖАН"),
                ("AX", "АЛАНДСКИЕ ОСТРОВА"),
                ("AL", "АЛБАНИЯ"),
                ("DZ", "АЛЖИР"),
                ("AS", "АМЕРИКАНСКОЕ САМОА"),
                ("AI", "АНГИЛЬЯ (БРИТ.)"),
                ("AO", "АНГОЛА"),
                ("AD", "АНДОРРА"),
                ("AQ", "АНТАРКТИДА"),
                ("AG", "АНТИГУА И БАРБУДА"),
                ("AR", "АРГЕНТИНА"),
                ("AM", "АРМЕНИЯ"),
                ("AW", "АРУБА"),
                ("AF", "АФГАНИСТАН"),
                ("BS", "БАГАМЫ"),
                ("BD", "БАНГЛАДЕШ"),
                ("BB", "БАРБАДОС"),
                ("BH", "БАХРЕЙН"),
                ("BY", "БЕЛАРУСЬ"),
                ("BZ", "БЕЛИЗ"),
                ("BE", "БЕЛЬГИЯ"),
                ("BJ", "БЕНИН"),
                ("BM", "БЕРМУДЫ"),
                ("BG", "БОЛГАРИЯ"),
                ("BO", "БОЛИВИЯ"),
                ("BQ", "БОНЭЙР, СИНТ-ЭСТАТИУС И САБА"),
                ("BA", "БОСНИЯ И ГЕРЦЕГОВИНА"),
                ("BW", "БОТСВАНА"),
                ("BR", "БРАЗИЛИЯ"),
                ("IO", "БРИТАНСКАЯ ТЕРРИТОРИЯ В ИНДИЙСКОМ ОКЕАНЕ"),
                ("BN", "БРУНЕЙ-ДАРУССАЛАМ"),
                ("BV", "БУВЕ"),
                ("BF", "БУРКИНА-ФАСО"),
                ("BI", "БУРУНДИ"),
                ("BT", "БУТАН"),
                ("VU", "ВАНУАТУ"),
                ("GB", "ВЕЛИКОБРИТАНИЯ"),
                ("HU", "ВЕНГРИЯ"),
                ("VE", "ВЕНЕСУЭЛА"),
                ("VG", "ВИРГИНСКИЕ ОСТРОВА (БРИТ.)"),
                ("VI", "ВИРГИНСКИЕ ОСТРОВА, США"),
                ("VN", "ВЬЕТНАМ"),
                ("GA", "ГАБОН"),
                ("HT", "ГАИТИ"),
                ("GY", "ГАЙАНА"),
                ("GM", "ГАМБИЯ"),
                ("GH", "ГАНА"),
                ("GP", "ГВАДЕЛУПА"),
                ("GT", "ГВАТЕМАЛА"),
                ("GN", "ГВИНЕЯ"),
                ("GW", "ГВИНЕЯ-БИСАУ"),
                ("DE", "ГЕРМАНИЯ"),
                ("GG", "ГЕРНСИ"),
                ("GI", "ГИБРАЛТАР (БРИТ.)"),
                ("HN", "ГОНДУРАС"),
                ("HK", "ГОНКОНГ"),
                ("GD", "ГРЕНАДА"),
                ("GL", "ГРЕНЛАНДИЯ"),
                ("GR", "ГРЕЦИЯ"),
                ("GE", "ГРУЗИЯ"),
                ("GU", "ГУАМ (США)"),
                ("DK", "ДАНИЯ"),
                ("CD", "ДЕМОКРАТИЧЕСКАЯ РЕСПУБЛИКА КОНГО"),
                ("JE", "ДЖЕРСИ"),
                ("DJ", "ДЖИБУТИ"),
                ("DM", "ДОМИНИКА"),
                ("DO", "ДОМИНИКАHСКАЯ РЕСПУБЛИКА"),
                ("EU", "ЕВРОПЕЙСКИЙ СОЮЗ"),
                ("EG", "ЕГИПЕТ"),
                ("ZM", "ЗАМБИЯ"),
                ("EH", "ЗАПАДНАЯ САХАРА"),
                ("ZW", "ЗИМБАБВЕ"),
                ("IL", "ИЗРАИЛЬ"),
                ("IN", "ИНДИЯ"),
                ("ID", "ИНДОНЕЗИЯ"),
                ("JO", "ИОРДАНИЯ"),
                ("IQ", "ИРАК, РЕСПУБЛИКА ИРАК"),
                ("IR", "ИРАН, ИСЛАМСКАЯ РЕСПУБЛИКА"),
                ("IE", "ИРЛАНДИЯ"),
                ("IS", "ИСЛАНДИЯ"),
                ("ES", "ИСПАНИЯ"),
                ("IT", "ИТАЛИЯ"),
                ("YE", "ЙЕМЕН"),
                ("CV", "КАБО-ВЕРДЕ"),
                ("KZ", "КАЗАХСТАН"),
                ("KH", "КАМБОДЖА"),
                ("CM", "КАМЕРУН"),
                ("CA", "КАНАДА"),
                ("QA", "КАТАР"),
                ("KE", "КЕНИЯ"),
                ("CY", "КИПР"),
                ("KI", "КИРИБАТИ"),
                ("CN", "КИТАЙ"),
                ("CC", "КОКОСОВЫЕ (КИЛИНГ) ОСТРОВА"),
                ("CO", "КОЛУМБИЯ"),
                ("KM", "КОМОРЫ"),
                ("CG", "КОНГО"),
                ("KP", "КОРЕЯ, НАРОДНО-ДЕМОКРАТИЧЕСКАЯ РЕСПУБЛИКА"),
                ("CR", "КОСТА-РИКА"),
                ("CI", "КОТ-Д'ИВУАР"),
                ("CU", "КУБА"),
                ("KW", "КУВЕЙТ"),
                ("KG", "КЫРГЫЗСТАН"),
                ("CW", "КЮРАСАО"),
                ("LA", "ЛАОССАЯ НАРОДНО-ДЕМОКРАТИЧЕСКАЯ РЕСПУБЛИКА"),
                ("LS", "ЛЕСОТО"),
                ("LR", "ЛИБЕРИЯ"),
                ("LB", "ЛИВАН"),
                ("LY", "ЛИВИЯ"),
                ("LT", "ЛИТВА"),
                ("LI", "ЛИХТЕНШТЕЙН"),
                ("LU", "ЛЮКСЕМБУРГ"),
                ("MU", "МАВРИКИЙ"),
                ("MR", "МАВРИТАНИЯ"),
                ("MG", "МАДАГАСКАР"),
                ("YT", "МАЙОТТА"),
                ("MO", "МАКАО"),
                ("MK", "МАКЕДОНИЯ"),
                ("MW", "МАЛАВИ"),
                ("MY", "МАЛАЙЗИЯ"),
                ("ML", "МАЛИ"),
                ("UM", "МАЛЫЕ ТИХООКЕАН.ОТДАЛЕН.ОСТ-ВА С.Ш."),
                ("MV", "МАЛЬДИВЫ"),
                ("MT", "МАЛЬТА"),
                ("MA", "МАРОККО"),
                ("MQ", "МАРТИНИКА"),
                ("MH", "МАРШАЛЛОВЫ ОСТРОВА"),
                ("MX", "МЕКСИКА"),
                ("FM", "МИКРОНЕЗИЯ, ФЕДЕРАТИВНЫЕ ШТАТЫ"),
                ("MZ", "МОЗАМБИК"),
                ("MD", "МОЛДОВА, РЕСПУБЛИКА"),
                ("MC", "МОНАКО"),
                ("MN", "МОНГОЛИЯ"),
                ("MS", "МОНТСЕРРАТ"),
                ("MM", "МЬЯНМА"),
                ("NA", "НАМИБИЯ"),
                ("NR", "НАУРУ"),
                ("NP", "НЕПАЛ"),
                ("NE", "НИГЕР"),
                ("NG", "НИГЕРИЯ"),
                ("NL", "НИДЕРЛАНДЫ"),
                ("NI", "НИКАРАГУА"),
                ("NU", "НИУЭ"),
                ("NZ", "НОВАЯ ЗЕЛАНДИЯ"),
                ("NC", "НОВАЯ КАЛЕДОНИЯ"),
                ("NO", "НОРВЕГИЯ"),
                ("AE", "ОБЪЕДИНЕННЫЕ АРАБСКИЕ ЭМИРАТЫ"),
                ("OM", "ОМАН"),
                ("IM", "ОСТРОВ МЭН"),
                ("NF", "ОСТРОВ НОРФОЛК"),
                ("CX", "ОСТРОВ РОЖДЕСТВА"),
                ("SH", "ОСТРОВ СВЯТОЙ ЕЛЕНЫ"),
                ("HM", "ОСТРОВ ХЕРД И ОСТРОВА МАКДОНАЛЬД"),
                ("KY", "ОСТРОВА КАЙМАН"),
                ("CK", "ОСТРОВА КУКА"),
                ("TC", "ОСТРОВА ТЕРКС И КАЙКОС"),
                ("PK", "ПАКИСТАН"),
                ("PW", "ПАЛАУ"),
                ("PS", "ПАЛЕСТИНСКАЯ ТЕРРИТОРИЯ, ОККУПИРОВАННАЯ"),
                ("PA", "ПАНАМА"),
                ("VA", "ПАПСКИЙ ПРЕСТОЛ(ГОС.-ГОРОД ВАТИКАН)"),
                ("PG", "ПАПУА-НОВАЯ ГВИНЕЯ"),
                ("PY", "ПАРАГВАЙ"),
                ("PE", "ПЕРУ"),
                ("PN", "ПИТКЕРН"),
                ("PL", "ПОЛЬША"),
                ("PT", "ПОРТУГАЛИЯ"),
                ("PR", "ПУЭРТО-РИКО"),
                ("KR", "РЕСПУБЛИКА КОРЕЯ"),
                ("LV", "РЕСПУБЛИКА ЛАТВИЯ"),
                ("RE", "РЕЮНЬОН"),
                ("RU", "РОССИЯ"),
                ("RW", "РУАНДА"),
                ("RO", "РУМЫНИЯ"),
                ("SM", "САH-МАРИHО"),
                ("WS", "САМОА"),
                ("ST", "САН-ТОМЕ И ПРИНСИПИ"),
                ("SA", "САУДОВСКАЯ АРАВИЯ"),
                ("SZ", "СВАЗИЛЕНД"),
                ("VC", "СЕHТ-ВИНСЕНТ И ГРЕНАДИНЫ"),
                ("LC", "СЕHТ-ЛЮСИЯ"),
                ("MP", "СЕВЕРНЫЕ МАРИАНСКИЕ ОСТРОВА"),
                ("SC", "СЕЙШЕЛЫ"),
                ("BL", "СЕН-БАРТЕЛЕМИ"),
                ("SN", "СЕНЕГАЛ"),
                ("MF", "СЕН-МАРТЕН"),
                ("SX", "СЕН-МАРТЕН (нидерландская часть)"),
                ("PM", "СЕН-ПЬЕР И МИКЕЛОН"),
                ("KN", "СЕНТ-КИТС И НЕВИС"),
                ("RS", "СЕРБИЯ"),
                ("SG", "СИНГАПУР"),
                ("SY", "СИРИЙСКАЯ АРАБСКАЯ РЕСПУБЛИКА"),
                ("SK", "СЛОВАКИЯ"),
                ("SI", "СЛОВЕНИЯ"),
                ("US", "СОЕДИНЕННЫЕ ШТАТЫ АМЕРИКИ"),
                ("SB", "СОЛОМОНОВЫ ОСТРОВА"),
                ("SO", "СОМАЛИ"),
                ("SD", "СУДАН"),
                ("SR", "СУРИНАМ"),
                ("SL", "СЬЕРРА-ЛЕОНЕ"),
                ("TJ", "ТАДЖИКИСТАН"),
                ("TH", "ТАИЛАНД"),
                ("TW", "ТАЙВАНЬ (КИТАЙ)"),
                ("TZ", "ТАНЗАНИЯ, ОБЪЕДИНЕННАЯ РЕСПУБЛИКА"),
                ("TL", "ТИМОР-ЛЕСТЕ"),
                ("TG", "ТОГО"),
                ("TK", "ТОКЕЛАУ"),
                ("TO", "ТОНГА"),
                ("TT", "ТРИНИДАД И ТОБАГО"),
                ("TV", "ТУВАЛУ"),
                ("TN", "ТУНИС"),
                ("TM", "ТУРКМЕНИСТАН"),
                ("TR", "ТУРЦИЯ"),
                ("UG", "УГАНДА"),
                ("UZ", "УЗБЕКИСТАН"),
                ("UA", "УКРАИНА"),
                ("WF", "УОЛЛИС И ФУТУНА"),
                ("UY", "УРУГВАЙ"),
                ("FO", "ФАРЕРСКИЕ ОСТРОВА"),
                ("FJ", "ФИДЖИ"),
                ("PH", "ФИЛИППИНЫ"),
                ("FI", "ФИНЛЯНДИЯ"),
                ("FK", "ФОЛКЛЕНДСКИЕ ОСТРОВА (МАЛЬВИНСКИЕ)"),
                ("FR", "ФРАНЦИЯ"),
                ("GF", "ФРАНЦУЗСКАЯ ГВИАНА"),
                ("PF", "ФРАНЦУЗСКАЯ ПОЛИНЕЗИЯ"),
                ("TF", "ФРАНЦУЗСКИЕ ЮЖНЫЕ ТЕРРИТОРИИ"),
                ("HR", "ХОРВАТИЯ"),
                ("CF", "ЦЕНТРАЛЬНО-АФРИКАНСКАЯ РЕСПУБЛИКА"),
                ("TD", "ЧАД"),
                ("ME", "ЧЕРНОГОРИЯ"),
                ("CZ", "ЧЕШСКАЯ РЕСПУБЛИКА"),
                ("CL", "ЧИЛИ"),
                ("CH", "ШВЕЙЦАРИЯ"),
                ("SE", "ШВЕЦИЯ"),
                ("SJ", "ШПИЦБЕРГЕН И ЯН МАЙЕН"),
                ("LK", "ШРИ-ЛАНКА"),
                ("EC", "ЭКВАДОР"),
                ("GQ", "ЭКВАТОРИАЛЬНАЯ ГВИНЕЯ"),
                ("SV", "ЭЛЬ-САЛЬВАДОР"),
                ("ER", "ЭРИТРЕЯ"),
                ("EE", "ЭСТОНИЯ"),
                ("ET", "ЭФИОПИЯ"),
                ("GS", "ЮЖН.ДЖОРДЖИЯ И ЮЖН.САНДВИЧ.ОСТРОВА"),
                ("ZA", "ЮЖНАЯ АФРИКА"),
                ("JM", "ЯМАЙКА"),
                ("JP", "ЯПОНИЯ")
            ]
            
            for code, name in countries:
                cursor.execute("""
                    INSERT INTO countries (code, name)
                    VALUES (?, ?)
                """, (code, name))
            
            self.conn.commit()
            logger.info("Значения стран мира по умолчанию добавлены")
    
    def insert_default_order_statuses(self):
        """Добавление стандартных статусов заказов"""
        cursor = self.conn.cursor()
        
        # Стандартные статусы заказов
        default_statuses = [
            ("CREATED", "Заказ создан", "Заказ создан в системе"),
            ("PENDING", "Заказ ожидает подтверждения", "Заказ ожидает подтверждения в системе маркировки"),
            ("DECLINED", "Заказ не подтверждён", "Заказ не подтверждён в системе маркировки"),
            ("APPROVED", "Заказ подтверждён", "Заказ подтверждён в системе маркировки"),
            ("READY", "Заказ готов", "Заказ готов к использованию"),
            ("CLOSED", "Заказ закрыт", "Заказ закрыт (обработан)")
        ]
        
        # Проверяем, какие коды статусов уже существуют в базе
        cursor.execute("SELECT code FROM order_statuses")
        existing_codes = [row[0] for row in cursor.fetchall()]
        
        # Добавляем только отсутствующие статусы
        added_count = 0
        for code, name, description in default_statuses:
            if code not in existing_codes:
                cursor.execute(
                    "INSERT INTO order_statuses (code, name, description) VALUES (?, ?, ?)",
                    (code, name, description)
                )
                added_count += 1
                logger.info(f"Добавлен стандартный статус заказа: {code} - {name}")
        
        if added_count > 0:
            # Явно сохраняем изменения
            self.conn.commit()
            logger.info(f"Добавлено {added_count} стандартных статусов заказов")
        
        return added_count > 0
    
    # Методы для работы с заказами
    def add_order(self, order_number: str, timestamp: str = None, expected_complete: int = None, status: str = "Не определен") -> Order:
        """Добавление заказа в базу данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO orders (order_number, timestamp, expected_complete, status) VALUES (?, ?, ?, ?)",
            (order_number, timestamp, expected_complete, status)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM orders WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return Order(row["id"], row["order_number"], row["timestamp"], row["expected_complete"], row["status"], row["created_at"])
    
    def get_orders(self) -> List[Order]:
        """Получение списка заказов из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        return [Order(row["id"], row["order_number"], row["timestamp"], row["expected_complete"], row["status"], row["created_at"]) for row in rows]
    
    def add_order_product(self, order_id: int, gtin: str, quantity: int) -> Dict[str, Any]:
        """Добавление товара в заказ"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO order_products (order_id, gtin, quantity) VALUES (?, ?, ?)",
            (order_id, gtin, quantity)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM order_products WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return dict(row)
    
    def get_order_products(self, order_id: int) -> List[Dict[str, Any]]:
        """Получение товаров заказа"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT op.*, n.name as product_name FROM order_products op " +
            "LEFT JOIN nomenclature n ON op.gtin = n.gtin " +
            "WHERE op.order_id = ?",
            (order_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Методы для работы с подключениями
    def add_connection(self, name: str, url: str) -> Connection:
        """Добавление подключения в базу данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO connections (name, url) VALUES (?, ?)",
            (name, url)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM connections WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return Connection(row["id"], row["name"], row["url"], bool(row["is_active"]))
    
    def update_connection(self, connection_id: int, name: str, url: str) -> Connection:
        """Обновление подключения в базе данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE connections SET name = ?, url = ? WHERE id = ?",
            (name, url, connection_id)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM connections WHERE id = ?",
            (connection_id,)
        )
        row = cursor.fetchone()
        return Connection(row["id"], row["name"], row["url"], bool(row["is_active"]))
    
    def delete_connection(self, connection_id: int) -> None:
        """Удаление подключения из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM connections WHERE id = ?",
            (connection_id,)
        )
        self.conn.commit()
    
    def get_connections(self) -> List[Connection]:
        """Получение списка подключений из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM connections")
        rows = cursor.fetchall()
        return [Connection(row["id"], row["name"], row["url"], bool(row["is_active"])) for row in rows]
    
    def get_connection_by_id(self, connection_id: int) -> Optional[Connection]:
        """Получение подключения по ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM connections WHERE id = ?",
            (connection_id,)
        )
        row = cursor.fetchone()
        if row:
            return Connection(row["id"], row["name"], row["url"], bool(row["is_active"]))
        return None
    
    def get_active_connection(self) -> Optional[Connection]:
        """Получение активного подключения"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM connections WHERE is_active = 1")
        row = cursor.fetchone()
        if row:
            return Connection(row["id"], row["name"], row["url"], True)
        return None
    
    def set_active_connection(self, connection_id: int) -> None:
        """Установка активного подключения"""
        cursor = self.conn.cursor()
        # Сначала сбрасываем все активные подключения
        cursor.execute("UPDATE connections SET is_active = 0")
        # Затем устанавливаем новое активное подключение
        cursor.execute(
            "UPDATE connections SET is_active = 1 WHERE id = ?",
            (connection_id,)
        )
        self.conn.commit()
    
    # Методы для работы с учетными данными
    def add_credentials(self, omsid: str, token: str, gln: str, connection_id: int = None) -> Credentials:
        """Добавление новых учетных данных
        
        Args:
            omsid: OMS ID
            token: Токен
            gln: GLN
            connection_id: ID подключения (опционально)
            
        Returns:
            Credentials: Объект учетных данных
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO credentials (omsid, token, gln) VALUES (?, ?, ?)",
            (omsid, token, gln)
        )
        self.conn.commit()
        credentials_id = cursor.lastrowid
        
        # Если указан connection_id, связываем учетные данные с подключением
        if connection_id:
            try:
                cursor.execute(
                    "INSERT INTO credential_connections (credential_id, connection_id) VALUES (?, ?)",
                    (credentials_id, connection_id)
                )
                self.conn.commit()
            except sqlite3.Error as e:
                # Если таблицы связей нет, создаем ее
                if "no such table" in str(e):
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS credential_connections (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            credential_id INTEGER,
                            connection_id INTEGER,
                            FOREIGN KEY (credential_id) REFERENCES credentials (id),
                            FOREIGN KEY (connection_id) REFERENCES connections (id)
                        )
                    ''')
                    self.conn.commit()
                    # И пробуем снова вставить запись
                    cursor.execute(
                        "INSERT INTO credential_connections (credential_id, connection_id) VALUES (?, ?)",
                        (credentials_id, connection_id)
                    )
                    self.conn.commit()
        
        # Возвращаем объект учетных данных
        return Credentials(id=credentials_id, omsid=omsid, token=token, gln=gln)
    
    def update_credentials(self, credentials_id: int, omsid: str, token: str, gln: str) -> Credentials:
        """Обновление учетных данных в базе данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE credentials SET omsid = ?, token = ?, gln = ? WHERE id = ?",
            (omsid, token, gln, credentials_id)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT c.* FROM credentials c WHERE c.id = ?",
            (credentials_id,)
        )
        row = cursor.fetchone()
        
        return Credentials(row["id"], row["omsid"], row["token"], row["gln"])
    
    def delete_credentials(self, credentials_id: int) -> None:
        """Удаление учетных данных из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM credentials WHERE id = ?",
            (credentials_id,)
        )
        self.conn.commit()
    
    def get_credentials(self) -> List[Credentials]:
        """Получение списка учетных данных из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials")
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            credentials = Credentials(row["id"], row["omsid"], row["token"], row["gln"])
            result.append(credentials)
        
        return result
    
    def get_credentials_by_id(self, credentials_id: int) -> Optional[Credentials]:
        """Получение учетных данных по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials WHERE id = ?", (credentials_id,))
        row = cursor.fetchone()
        
        if row:
            return Credentials(row["id"], row["omsid"], row["token"], row["gln"])
        
        return None
    
    def get_credentials_for_connection(self, connection_id: int) -> List[Credentials]:
        """Получение учетных данных для конкретного подключения"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials WHERE connection_id = ?", (connection_id,))
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            credentials = Credentials(row["id"], row["omsid"], row["token"], row["gln"])
            result.append(credentials)
        
        return result
    
    # Методы для работы с номенклатурой
    def add_nomenclature(self, name: str, gtin: str, product_group: str = "") -> Nomenclature:
        """Добавление номенклатуры в базу данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO nomenclature (name, gtin, product_group) VALUES (?, ?, ?)",
            (name, gtin, product_group)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM nomenclature WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        product_group_value = row["product_group"] if "product_group" in row.keys() else ""
        return Nomenclature(row["id"], row["name"], row["gtin"], product_group_value)
    
    def update_nomenclature(self, nomenclature_id: int, name: str, gtin: str, product_group: str = "") -> Nomenclature:
        """Обновление номенклатуры в базе данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE nomenclature SET name = ?, gtin = ?, product_group = ? WHERE id = ?",
            (name, gtin, product_group, nomenclature_id)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM nomenclature WHERE id = ?",
            (nomenclature_id,)
        )
        row = cursor.fetchone()
        product_group_value = row["product_group"] if "product_group" in row.keys() else ""
        return Nomenclature(row["id"], row["name"], row["gtin"], product_group_value)
    
    def delete_nomenclature(self, nomenclature_id: int) -> None:
        """Удаление номенклатуры из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM nomenclature WHERE id = ?",
            (nomenclature_id,)
        )
        self.conn.commit()
    
    def get_nomenclature(self) -> List[Nomenclature]:
        """Получение списка номенклатуры из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nomenclature")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            product_group_value = row["product_group"] if "product_group" in row.keys() else ""
            result.append(Nomenclature(row["id"], row["name"], row["gtin"], product_group_value))
        return result
    
    def get_nomenclature_by_id(self, nomenclature_id: int) -> Optional[Nomenclature]:
        """Получение номенклатуры по ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM nomenclature WHERE id = ?",
            (nomenclature_id,)
        )
        row = cursor.fetchone()
        if row:
            product_group_value = row["product_group"] if "product_group" in row.keys() else ""
            return Nomenclature(row["id"], row["name"], row["gtin"], product_group_value)
        return None
    
    # Методы для работы с расширениями API
    def get_extensions(self) -> List[Extension]:
        """Получение списка расширений API из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM extensions")
        rows = cursor.fetchall()
        return [Extension(row["id"], row["code"], row["name"], bool(row["is_active"])) for row in rows]
    
    def get_active_extension(self) -> Optional[Extension]:
        """Получение активного расширения API"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM extensions WHERE is_active = 1")
        row = cursor.fetchone()
        if row:
            return Extension(row["id"], row["code"], row["name"], True)
        return None
    
    def set_active_extension(self, extension_id: int) -> None:
        """Установка активного расширения API"""
        cursor = self.conn.cursor()
        # Сначала сбрасываем все активные расширения
        cursor.execute("UPDATE extensions SET is_active = 0")
        # Затем устанавливаем новое активное расширение
        cursor.execute(
            "UPDATE extensions SET is_active = 1 WHERE id = ?",
            (extension_id,)
        )
        self.conn.commit()
    
    # Методы для работы с настройками
    def set_setting(self, key: str, value: str) -> None:
        """Установка значения настройки"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Получение значения настройки"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row["value"]
        return default
    
    # Методы для работы с логами API
    def add_api_log(self, method, url, request, response, status_code, success=True, description=None):
        """Добавление записи в лог API-запросов"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO api_logs (method, url, request, response, status_code, success, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (method, url, request, response, status_code, 1 if success else 0, description)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM api_logs WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "method": row["method"],
            "url": row["url"],
            "request": row["request"],
            "response": row["response"],
            "status_code": row["status_code"],
            "success": bool(row["success"]),
            "description": row["description"] if "description" in row.keys() else None,
            "timestamp": row["timestamp"]
        }
    
    def get_api_logs(self, limit=100, offset=0, success=None, method=None, url_pattern=None, date_from=None, date_to=None):
        """Получение списка логов API-запросов с фильтрацией"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM api_logs WHERE 1=1"
        params = []
        
        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)
            
        if method is not None:
            query += " AND method = ?"
            params.append(method)
            
        if url_pattern is not None:
            query += " AND url LIKE ?"
            params.append(f"%{url_pattern}%")
            
        if date_from is not None:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())
            
        if date_to is not None:
            query += " AND timestamp <= ?"
            params.append(date_to.isoformat())
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            log_entry = {
                "id": row["id"],
                "method": row["method"],
                "url": row["url"],
                "request": row["request"],
                "response": row["response"],
                "status_code": row["status_code"],
                "success": bool(row["success"]),
                "timestamp": row["timestamp"]
            }
            # Добавляем поле description, если оно есть
            if "description" in row.keys():
                log_entry["description"] = row["description"]
            result.append(log_entry)
        return result
    
    def get_api_log_by_id(self, log_id):
        """Получение записи лога API-запроса по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM api_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        log_entry = {
            "id": row["id"],
            "method": row["method"],
            "url": row["url"],
            "request": row["request"],
            "response": row["response"],
            "status_code": row["status_code"],
            "success": bool(row["success"]),
            "timestamp": row["timestamp"]
        }
        
        # Добавляем поле description, если оно есть
        if "description" in row.keys():
            log_entry["description"] = row["description"]
            
        return log_entry
    
    def count_api_logs(self, date_from=None, success=None):
        """Подсчет количества логов API-запросов"""
        cursor = self.conn.cursor()
        
        query = "SELECT COUNT(*) as count FROM api_logs WHERE 1=1"
        params = []
        
        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)
            
        if date_from is not None:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row["count"] if row else 0
        
    def get_method_stats(self, date_from=None):
        """Получение статистики по HTTP-методам"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT method, COUNT(*) as count, 
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as fail_count
            FROM api_logs 
            WHERE 1=1
        """
        params = []
        
        if date_from is not None:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())
            
        query += " GROUP BY method"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            result.append({
                "method": row["method"],
                "count": row["count"],
                "success_count": row["success_count"],
                "fail_count": row["fail_count"],
                "success_rate": (row["success_count"] / row["count"] * 100) if row["count"] > 0 else 0
            })
            
        return result
        
    def get_url_stats(self, date_from=None):
        """Получение статистики по URL"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT url, COUNT(*) as count, 
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as fail_count
            FROM api_logs 
            WHERE 1=1
        """
        params = []
        
        if date_from is not None:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())
            
        query += " GROUP BY url"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            result.append({
                "url": row["url"],
                "count": row["count"],
                "success_count": row["success_count"],
                "fail_count": row["fail_count"],
                "success_rate": (row["success_count"] / row["count"] * 100) if row["count"] > 0 else 0
            })
            
        return result
        
    def delete_api_logs_by_ids(self, log_ids):
        """Удаление логов API-запросов по ID"""
        if not log_ids:
            return 0
            
        cursor = self.conn.cursor()
        placeholders = ','.join(['?' for _ in log_ids])
        cursor.execute(f"DELETE FROM api_logs WHERE id IN ({placeholders})", log_ids)
        self.conn.commit()
        return cursor.rowcount
        
    def delete_api_logs_before_date(self, before_date):
        """Удаление логов API-запросов до указанной даты"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM api_logs WHERE timestamp < ?", (before_date.isoformat(),))
        self.conn.commit()
        return cursor.rowcount
    
    def get_emission_types(self) -> List[EmissionType]:
        """Получение всех типов эмиссии"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, code, name, product_group FROM emission_types")
        rows = cursor.fetchall()
        return [EmissionType(row["id"], row["code"], row["name"], row["product_group"]) for row in rows]
    
    def get_emission_types_for_product_group(self, product_group: str) -> List[EmissionType]:
        """Получение типов эмиссии для указанной товарной группы"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, code, name, product_group FROM emission_types
            WHERE product_group IS NULL OR product_group = ?
        """, (product_group,))
        rows = cursor.fetchall()
        return [EmissionType(row["id"], row["code"], row["name"], row["product_group"]) for row in rows]
    
    def get_countries(self) -> List[Country]:
        """Получение всех стран мира"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, code, name FROM countries ORDER BY name")
        rows = cursor.fetchall()
        return [Country(row["id"], row["code"], row["name"]) for row in rows]
    
    def get_country_by_code(self, code: str) -> Optional[Country]:
        """Получение страны по коду"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, code, name FROM countries WHERE code = ?", (code,))
        row = cursor.fetchone()
        if row:
            return Country(row["id"], row["code"], row["name"])
        return None
    
    def get_order_statuses(self) -> List[OrderStatus]:
        """Получение списка статусов заказов"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM order_statuses")
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            status = OrderStatus(
                row["id"],
                row["code"],
                row["name"],
                row["description"] if "description" in row.keys() else ""
            )
            result.append(status)
        
        return result
    
    def get_order_status_by_code(self, code: str) -> Optional[OrderStatus]:
        """Получение статуса заказа по коду"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM order_statuses WHERE code = ?", (code,))
        row = cursor.fetchone()
        
        if row:
            return OrderStatus(
                row["id"],
                row["code"],
                row["name"],
                row["description"] if "description" in row.keys() else ""
            )
        
        return None
    
    def add_order_status(self, code: str, name: str, description: str = "") -> OrderStatus:
        """Добавление статуса заказа в базу данных"""
        try:
            # Проверяем, что код и название не пустые
            if not code or not name:
                raise ValueError("Код и название статуса не могут быть пустыми")
            
            # Проверяем, что код уникальный
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM order_statuses WHERE code = ?", (code,))
            if cursor.fetchone():
                raise ValueError(f"Статус с кодом '{code}' уже существует")
            
            # Добавляем статус заказа
            cursor.execute("""
                INSERT INTO order_statuses (code, name, description)
                VALUES (?, ?, ?)
            """, (code, name, description))
            
            # Получаем ID добавленного статуса
            status_id = cursor.lastrowid
            
            # Явно сохраняем изменения
            self.conn.commit()
            
            # Создаем и возвращаем объект статуса
            return OrderStatus(
                id=status_id,
                code=code,
                name=name,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении статуса заказа: {str(e)}")
            raise
    
    def update_order_status(self, status_id: int, code: str, name: str, description: str = "") -> OrderStatus:
        """Обновление статуса заказа в базе данных"""
        try:
            # Проверяем, что код и название не пустые
            if not code or not name:
                raise ValueError("Код и название статуса не могут быть пустыми")
            
            # Проверяем, что код уникальный (исключая текущий статус)
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id FROM order_statuses 
                WHERE code = ? AND id != ?
            """, (code, status_id))
            if cursor.fetchone():
                raise ValueError(f"Статус с кодом '{code}' уже существует")
            
            # Обновляем статус заказа
            cursor.execute("""
                UPDATE order_statuses 
                SET code = ?, name = ?, description = ?
                WHERE id = ?
            """, (code, name, description, status_id))
            
            # Явно сохраняем изменения
            self.conn.commit()
            
            # Создаем и возвращаем объект статуса
            return OrderStatus(
                id=status_id,
                code=code,
                name=name,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса заказа: {str(e)}")
            raise
    
    def delete_order_status(self, status_id: int) -> None:
        """Удаление статуса заказа из базы данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM order_statuses WHERE id = ?", (status_id,))
            
            # Явно сохраняем изменения
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при удалении статуса заказа: {str(e)}")
            raise
    
    # Методы для работы с API заказами
    def save_api_orders(self, api_orders: List[APIOrder]) -> List[APIOrder]:
        """Сохранение API заказов в базу данных
        
        Данные не удаляются полностью, а обновляются:
        - Существующие заказы обновляются
        - Новые заказы добавляются
        - Заказы, отсутствующие в новом списке, помечаются как устаревшие
        """
        try:
            cursor = self.conn.cursor()
            
            # Получаем текущие order_id из базы данных
            cursor.execute("SELECT order_id, order_status FROM api_orders")
            existing_orders = {row["order_id"]: row["order_status"] for row in cursor.fetchall()}
            
            # Новые order_id из полученного списка
            new_order_ids = [order.order_id for order in api_orders]
            
            # Определяем заказы, которые нужно пометить как устаревшие
            # (они есть в базе, но отсутствуют в новом списке)
            obsolete_order_ids = [order_id for order_id in existing_orders.keys() 
                                if order_id not in new_order_ids]
            
            # Помечаем устаревшие заказы (только если они не OBSOLETE уже)
            if obsolete_order_ids:
                current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                for order_id in obsolete_order_ids:
                    # Проверяем, не устарел ли заказ уже
                    if existing_orders[order_id] != "OBSOLETE":
                        cursor.execute(
                            "UPDATE api_orders SET order_status = 'OBSOLETE', order_status_description = ? WHERE order_id = ?",
                            (f"Устарел {current_time}", order_id)
                        )
                logger.info(f"Помечено устаревших заказов: {len(obsolete_order_ids)}")
            
            # Явно удаляем заказы с баферами без значений, таких как READY
            for order in api_orders:
                if not order.buffers and order.order_status == "READY":
                    # Если в ответе сервера буферы не определены, но статус READY,
                    # проверим наличие такого заказа в базе
                    cursor.execute(
                        "SELECT buffers FROM api_orders WHERE order_id = ? AND order_status = 'READY'",
                        (order.order_id,)
                    )
                    existing_order = cursor.fetchone()
                    
                    if existing_order and existing_order["buffers"]:
                        # Если заказ уже есть и в нем есть буферы, сохраняем их
                        try:
                            existing_buffers = json.loads(existing_order["buffers"])
                            if existing_buffers:
                                # Используем существующие буферы
                                order.buffers = existing_buffers
                                logger.info(f"Для заказа {order.order_id} использованы существующие буферы")
                        except:
                            logger.warning(f"Не удалось десериализовать буферы для {order.order_id}")
            
            # Добавляем новые заказы и обновляем существующие
            for order in api_orders:
                # Проверяем, существует ли заказ с таким order_id
                cursor.execute(
                    "SELECT id FROM api_orders WHERE order_id = ?",
                    (order.order_id,)
                )
                existing_order = cursor.fetchone()
                
                # Преобразуем буферы в JSON для хранения
                buffers_json = json.dumps(order.buffers)
                
                if existing_order:
                    # Обновляем существующий заказ
                    cursor.execute("""
                        UPDATE api_orders SET 
                            order_status = ?,
                            order_status_description = NULL,
                            created_timestamp = ?,
                            total_quantity = ?,
                            num_of_products = ?,
                            product_group_type = ?,
                            signed = ?,
                            verified = ?,
                            buffers = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE order_id = ?
                    """, (
                        order.order_status,
                        order.created_timestamp,
                        order.total_quantity,
                        order.num_of_products,
                        order.product_group_type,
                        order.signed,
                        order.verified,
                        buffers_json,
                        order.order_id
                    ))
                else:
                    # Добавляем новый заказ
                    cursor.execute("""
                        INSERT INTO api_orders (
                            order_id, order_status, created_timestamp,
                            total_quantity, num_of_products, product_group_type,
                            signed, verified, buffers, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        order.order_id, order.order_status, order.created_timestamp,
                        order.total_quantity, order.num_of_products, order.product_group_type,
                        order.signed, order.verified, buffers_json
                    ))
            
            # Явно сохраняем изменения
            self.conn.commit()
            
            # Получаем и возвращаем обновленный список заказов
            return self.get_api_orders()
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении API заказов: {str(e)}")
            raise
    
    def get_api_orders(self) -> List[APIOrder]:
        """Получение списка API заказов из базы данных"""
        try:
            # Сначала проверим колонки в таблице
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(api_orders)")
            columns = cursor.fetchall()
            column_names = [column["name"] for column in columns]
            
            # Добавим отсутствующие колонки, если это необходимо
            schema_updated = False
            if "order_status_description" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN order_status_description TEXT")
                schema_updated = True
            
            if "updated_at" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN updated_at TIMESTAMP")
                schema_updated = True
                
            if "buffers" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN buffers TEXT")
                schema_updated = True
                
            if schema_updated:
                self.conn.commit()
                logger.info("Автоматическое обновление схемы таблицы api_orders завершено")
            
            # Затем выполним запрос к таблице
            cursor.execute("SELECT * FROM api_orders ORDER BY created_timestamp DESC")
            rows = cursor.fetchall()
            
            api_orders = []
            for row in rows:
                try:
                    # Десериализуем буферы из JSON
                    buffers = []
                    if "buffers" in row.keys() and row["buffers"]:
                        try:
                            buffers = json.loads(row["buffers"])
                        except json.JSONDecodeError:
                            logger.warning(f"Не удалось десериализовать буферы для заказа {row['order_id']}")
                    
                    # Получаем дополнительные поля, если они есть
                    order_status_description = None
                    if "order_status_description" in row.keys():
                        order_status_description = row["order_status_description"]
                    
                    updated_at = None
                    if "updated_at" in row.keys():
                        updated_at = row["updated_at"]
                    
                    # Создаем объект API заказа
                    api_order = APIOrder(
                        order_id=row["order_id"],
                        order_status=row["order_status"],
                        created_timestamp=row["created_timestamp"],
                        total_quantity=row["total_quantity"],
                        num_of_products=row["num_of_products"],
                        product_group_type=row["product_group_type"],
                        signed=row["signed"],
                        verified=row["verified"],
                        buffers=buffers,
                        order_status_description=order_status_description,
                        updated_at=updated_at
                    )
                    api_order.id = row["id"]
                    api_orders.append(api_order)
                    
                except Exception as e:
                    logger.error(f"Ошибка при загрузке API заказа {row.get('order_id', 'Unknown')}: {str(e)}")
            
            return api_orders
        except Exception as e:
            logger.error(f"Ошибка при получении списка API заказов: {str(e)}")
            return []
    
    def delete_api_order(self, order_id: str) -> bool:
        """Удаление API заказа из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM api_orders WHERE order_id = ?", (order_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def migrate_api_order_structure(self):
        """Миграция структуры API заказов из старой (с отдельной таблицей буферов) в новую (с буферами в JSON)"""
        try:
            cursor = self.conn.cursor()
            
            # Проверяем наличие колонок в таблице api_orders
            cursor.execute("PRAGMA table_info(api_orders)")
            columns = cursor.fetchall()
            column_names = [column["name"] for column in columns]
            
            # Добавляем колонку buffers, если ее нет
            if "buffers" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN buffers TEXT")
                logger.info("Добавлена колонка buffers в таблицу api_orders")
            
            # Добавляем колонку order_status_description, если ее нет
            if "order_status_description" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN order_status_description TEXT")
                logger.info("Добавлена колонка order_status_description в таблицу api_orders")
            
            # Добавляем колонку updated_at, если ее нет
            if "updated_at" not in column_names:
                cursor.execute("ALTER TABLE api_orders ADD COLUMN updated_at TIMESTAMP")
                logger.info("Добавлена колонка updated_at в таблицу api_orders")
                
            # Проверяем наличие таблицы api_order_buffers
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_order_buffers'")
            if cursor.fetchone():
                logger.info("Обнаружена устаревшая таблица api_order_buffers, выполняется миграция данных")
                
                # Получаем все заказы
                cursor.execute("SELECT id, order_id FROM api_orders")
                orders = cursor.fetchall()
                
                for order in orders:
                    order_id = order["id"]
                    
                    # Получаем буферы для этого заказа
                    cursor.execute("SELECT * FROM api_order_buffers WHERE api_order_id = ?", (order_id,))
                    buffer_rows = cursor.fetchall()
                    
                    if buffer_rows:
                        # Преобразуем буферы в новый формат
                        buffers = []
                        for buffer_row in buffer_rows:
                            buffer = {
                                "orderId": order["order_id"],
                                "gtin": buffer_row["gtin"],
                                "leftInBuffer": -1,
                                "poolsExhausted": False,
                                "totalCodes": -1,
                                "unavailableCodes": -1,
                                "availableCodes": -1,
                                "totalPassed": -1,
                                "omsId": ""
                            }
                            buffers.append(buffer)
                        
                        # Сохраняем буферы в JSON формате
                        buffers_json = json.dumps(buffers)
                        cursor.execute("UPDATE api_orders SET buffers = ? WHERE id = ?", (buffers_json, order_id))
                
                # Обновляем updated_at для всех заказов
                cursor.execute("UPDATE api_orders SET updated_at = CURRENT_TIMESTAMP")
                
                # Сохраняем изменения
                self.conn.commit()
                logger.info("Миграция данных буферов завершена")
                
                # Удаляем устаревшую таблицу
                cursor.execute("DROP TABLE api_order_buffers")
                self.conn.commit()
                logger.info("Устаревшая таблица api_order_buffers удалена")
            
            # Сохраняем изменения, если произошли какие-либо изменения в структуре
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при миграции структуры API заказов: {str(e)}")
            # Продолжаем выполнение, так как это не критическая ошибка
    
    def __del__(self):
        """Закрытие соединения с базой данных при уничтожении объекта"""
        if hasattr(self, 'conn') and self.conn:
            try:
                # Явное сохранение всех изменений перед закрытием
                self.conn.commit()
                logger.info("Изменения в базе данных сохранены перед закрытием")
            except Exception as e:
                logger.error(f"Ошибка при сохранении изменений в базе данных: {str(e)}")
            finally:
                # Закрытие соединения
                self.conn.close()
                logger.info("Соединение с базой данных закрыто")
    
    def commit(self):
        """Явное сохранение изменений в базу данных"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.commit()
            logger.info("Изменения вручную сохранены в базу данных")