from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sqlite3
import logging
from typing import List, Optional, Dict, Any
from models.models import Order, Connection, Credentials, Nomenclature, Extension, EmissionType, Country

# Инициализация логгера
logger = logging.getLogger(__name__)

Base = declarative_base()

class OrderORM(Base):
    """Модель заказа в SQLAlchemy"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

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
    connection_id = Column(Integer, ForeignKey('connections.id'))
    connection = relationship("ConnectionORM")
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

class Database:
    """Класс для работы с базой данных"""
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.migrate_database()
        self.insert_default_extensions()
        self.insert_default_emission_types()
        self.insert_default_countries()
    
    def create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.conn.cursor()
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                connection_id INTEGER NULL,
                FOREIGN KEY (connection_id) REFERENCES connections (id)
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
        
        # Проверяем, есть ли колонка product_group в таблице nomenclature
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
                logger.error(f"Ошибка при добавлении колонки product_group: {str(e)}")
        
        # Проверяем, есть ли колонка description в таблице api_logs
        cursor.execute("PRAGMA table_info(api_logs)")
        columns = cursor.fetchall()
        column_names = [column["name"] for column in columns]
        
        # Если колонки нет, добавляем её
        if "description" not in column_names:
            try:
                cursor.execute("ALTER TABLE api_logs ADD COLUMN description TEXT")
                self.conn.commit()
                logger.info("Добавлена колонка description в таблицу api_logs")
            except Exception as e:
                logger.error(f"Ошибка при добавлении колонки description: {str(e)}")
    
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
    
    # Методы для работы с заказами
    def add_order(self, order_number: str, status: str) -> Order:
        """Добавление заказа в базу данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO orders (order_number, status) VALUES (?, ?)",
            (order_number, status)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT * FROM orders WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return Order(row["id"], row["order_number"], row["status"], row["created_at"])
    
    def get_orders(self) -> List[Order]:
        """Получение списка заказов из базы данных"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [Order(row["id"], row["order_number"], row["status"], row["created_at"]) for row in rows]
    
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
    def add_credentials(self, omsid: str, token: str, connection_id: Optional[int] = None) -> Credentials:
        """Добавление учетных данных в базу данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO credentials (omsid, token, connection_id) VALUES (?, ?, ?)",
            (omsid, token, connection_id)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT c.* FROM credentials c WHERE c.id = ?",
            (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        
        # Получаем информацию о подключении, если указан connection_id
        connection = None
        if connection_id:
            conn_cursor = self.conn.cursor()
            conn_cursor.execute(
                "SELECT * FROM connections WHERE id = ?",
                (connection_id,)
            )
            conn_row = conn_cursor.fetchone()
            if conn_row:
                connection = Connection(conn_row["id"], conn_row["name"], 
                                        conn_row["url"], bool(conn_row["is_active"]))
        
        return Credentials(row["id"], row["omsid"], row["token"], connection)
    
    def update_credentials(self, credentials_id: int, omsid: str, token: str) -> Credentials:
        """Обновление учетных данных в базе данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE credentials SET omsid = ?, token = ? WHERE id = ?",
            (omsid, token, credentials_id)
        )
        self.conn.commit()
        
        cursor.execute(
            "SELECT c.* FROM credentials c WHERE c.id = ?",
            (credentials_id,)
        )
        row = cursor.fetchone()
        
        # Получаем информацию о подключении, если указан connection_id
        connection = None
        if row["connection_id"]:
            conn_cursor = self.conn.cursor()
            conn_cursor.execute(
                "SELECT * FROM connections WHERE id = ?",
                (row["connection_id"],)
            )
            conn_row = conn_cursor.fetchone()
            if conn_row:
                connection = Connection(conn_row["id"], conn_row["name"], 
                                        conn_row["url"], bool(conn_row["is_active"]))
        
        return Credentials(row["id"], row["omsid"], row["token"], connection)
    
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
        
        # Получаем все подключения одним запросом для оптимизации
        conn_cursor = self.conn.cursor()
        conn_cursor.execute("SELECT * FROM connections")
        connections = {row["id"]: Connection(row["id"], row["name"], row["url"], bool(row["is_active"])) 
                      for row in conn_cursor.fetchall()}
        
        for row in rows:
            # Находим подключение, если оно указано
            connection = connections.get(row["connection_id"]) if row["connection_id"] else None
            credentials = Credentials(row["id"], row["omsid"], row["token"], connection)
            result.append(credentials)
        
        return result
    
    def get_credentials_by_id(self, credentials_id: int) -> Optional[Credentials]:
        """Получение учетных данных по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials WHERE id = ?", (credentials_id,))
        row = cursor.fetchone()
        
        if row:
            # Получаем информацию о подключении, если указан connection_id
            connection = None
            if row["connection_id"]:
                conn_cursor = self.conn.cursor()
                conn_cursor.execute(
                    "SELECT * FROM connections WHERE id = ?",
                    (row["connection_id"],)
                )
                conn_row = conn_cursor.fetchone()
                if conn_row:
                    connection = Connection(conn_row["id"], conn_row["name"], 
                                           conn_row["url"], bool(conn_row["is_active"]))
            
            return Credentials(row["id"], row["omsid"], row["token"], connection)
        
        return None
    
    def get_credentials_for_connection(self, connection_id: int) -> List[Credentials]:
        """Получение учетных данных для конкретного подключения"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials WHERE connection_id = ?", (connection_id,))
        rows = cursor.fetchall()
        
        # Получаем подключение
        conn_cursor = self.conn.cursor()
        conn_cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
        conn_row = conn_cursor.fetchone()
        connection = None
        if conn_row:
            connection = Connection(conn_row["id"], conn_row["name"], 
                                   conn_row["url"], bool(conn_row["is_active"]))
        
        result = []
        for row in rows:
            credentials = Credentials(row["id"], row["omsid"], row["token"], connection)
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
    
    def get_api_logs(self, limit=100, offset=0):
        """Получение списка логов API-запросов"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
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
        """Получение лога API-запроса по ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM api_logs WHERE id = ?",
            (log_id,)
        )
        row = cursor.fetchone()
        if row:
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
        return None
    
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
    
    def __del__(self):
        """Закрытие соединения с базой данных при уничтожении объекта"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close() 