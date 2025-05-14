from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                         QTableWidget, QTableWidgetItem, QComboBox, QFormLayout,
                         QLineEdit, QPushButton, QLabel, QMessageBox, QHeaderView,
                         QCheckBox, QGroupBox, QSpinBox, QDateEdit, QFileDialog, QMenu,
                         QDialog, QDialogButtonBox, QSplitter, QTextEdit, QInputDialog)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPoint, QDateTime, QTimer
from PyQt6.QtGui import QAction, QCursor, QColor, QIntValidator

from views.dialogs import EmissionOrderDialog, DisplayCodesDialog
from .dialogs import ConnectionDialog, CredentialsDialog, NomenclatureDialog, GetKMDialog, BaseDialog
import logging
import datetime
import json
from models.models import Extension, Nomenclature, EmissionType, Country
from typing import List
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    # Сигналы
    get_orders_signal = pyqtSignal(dict)
    get_order_details_signal = pyqtSignal(str)
    create_order_signal = pyqtSignal(dict)
    emit_order_signal = pyqtSignal(dict)
    settings_signal = pyqtSignal()
    get_registry_presets_signal = pyqtSignal()
    get_registry_by_id_signal = pyqtSignal(str)
    test_connection_signal = pyqtSignal()
    check_updates_signal = pyqtSignal()
    get_marking_codes_signal = pyqtSignal(dict)
    get_report_signal = pyqtSignal()  # Сигнал для получения отчета
    get_version_signal = pyqtSignal()  # Сигнал для получения версии
    
    # Сигналы для работы с заказами
    add_order_signal = pyqtSignal(str, str)
    ping_signal = pyqtSignal()
    get_orders_status_signal = pyqtSignal()  # Сигнал для получения статуса заказов
    create_emission_order_signal = pyqtSignal(dict)  # Сигнал для создания заказа на эмиссию кодов
    api_orders_signal = pyqtSignal()  # Сигнал для получения заказов API
    delete_api_order_signal = pyqtSignal(str)  # Сигнал для удаления API заказа
    get_km_from_order_signal = pyqtSignal(str, str, int)  # Сигнал для получения КМ из заказа
    
    # Сигналы для работы с подключениями
    add_connection_signal = pyqtSignal(str, str)
    edit_connection_signal = pyqtSignal(int, str, str)
    delete_connection_signal = pyqtSignal(int)
    set_active_connection_signal = pyqtSignal(int)
    
    # Сигналы для работы с учетными данными
    add_credentials_signal = pyqtSignal(str, str, str, str)  # omsid, token, gln, connection_id
    edit_credentials_signal = pyqtSignal(int, str, str, str)  # id, omsid, token, gln
    delete_credentials_signal = pyqtSignal(int)
    
    # Сигналы для работы с номенклатурой
    add_nomenclature_signal = pyqtSignal(str, str, str)  # name, gtin, product_group
    edit_nomenclature_signal = pyqtSignal(int, str, str, str)  # id, name, gtin, product_group
    delete_nomenclature_signal = pyqtSignal(int)
    
    # Сигналы для работы с расширениями API
    set_active_extension_signal = pyqtSignal(int)
    
    # Сигналы для работы с логами API
    load_api_logs_signal = pyqtSignal()
    get_api_log_details_signal = pyqtSignal(int, object, object)  # id, callback_request, callback_response
    export_api_descriptions_signal = pyqtSignal()  # Сигнал для экспорта описаний API в файл
    
    # Сигналы для работы со странами
    load_countries_signal = pyqtSignal()
    
    # Сигналы для работы со статусами заказов
    load_order_statuses_signal = pyqtSignal()
    add_order_status_signal = pyqtSignal(str, str, str)  # code, name, description
    edit_order_status_signal = pyqtSignal(int, str, str, str)  # id, code, name, description
    delete_order_status_signal = pyqtSignal(int)
    
    # Сигналы для работы с типами использования кодов маркировки
    load_usage_types_signal = pyqtSignal()  # Сигнал для загрузки типов использования
    add_usage_type_signal = pyqtSignal(str, str, str)  # code, name, description
    edit_usage_type_signal = pyqtSignal(int, str, str, str)  # id, code, name, description
    delete_usage_type_signal = pyqtSignal(int)  # id
    
    # Сигналы для работы с кодами маркировки
    mark_codes_as_used_signal = pyqtSignal(list)  # code_ids
    mark_codes_as_exported_signal = pyqtSignal(list)  # code_ids
    
    # Сигналы для работы с файлами агрегации
    load_aggregation_files_signal = pyqtSignal()  # Сигнал для загрузки файлов агрегации
    add_aggregation_file_signal = pyqtSignal(str, dict, str)  # filename, data, comment
    delete_aggregation_file_signal = pyqtSignal(int)  # file_id
    export_aggregation_file_signal = pyqtSignal(int, str)  # file_id, export_path
    send_utilisation_report_signal = pyqtSignal(dict)  # data
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление заказами")
        self.setMinimumSize(800, 600)
        
        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Создаем индикатор статуса API
        self.create_status_bar()
        
        # Создаем вкладки
        self.create_orders_tab()
        self.create_api_orders_tab()
        self.create_connections_tab()
        self.create_credentials_tab()
        self.create_nomenclature_tab()
        self.create_extensions_tab()
        self.create_api_logs_tab()
        self.create_countries_tab()
        self.create_order_statuses_tab()
        self.create_marking_codes_tab()
        self.create_aggregation_files_tab()  # Добавляем новую вкладку
        
        # Добавляем вкладки в виджет (только те, которые должны быть видны)
        self.tabs.addTab(self.orders_tab, "Заказы")
        self.tabs.addTab(self.api_orders_tab, "API Заказы")
        self.tabs.addTab(self.api_logs_tab, "Логи API")
        self.tabs.addTab(self.marking_codes_tab, "Коды маркировки")
        self.tabs.addTab(self.aggregation_files_tab, "Файлы агрегации")  # Добавляем новую вкладку
        
        # Создаем панель кнопок для вызова модальных окон
        toolbar = self.addToolBar("Панель инструментов")
        
        # Кнопка справочников
        catalogs_button = QPushButton("Справочники")
        catalogs_button.clicked.connect(self.show_catalogs_dialog)
        toolbar.addWidget(catalogs_button)
        
        # Кнопка настроек
        settings_button = QPushButton("Настройки")
        settings_button.clicked.connect(self.show_settings_dialog)
        toolbar.addWidget(settings_button)
        
        # Подключаем обработчик изменения активной вкладки
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def on_tab_changed(self, index):
        """Обработчик изменения активной вкладки в главном окне"""
        # Обновляем данные в зависимости от выбранной вкладки
        if index == 0:  # Заказы
            pass  # Обновление происходит через сигналы
        elif index == 1:  # API заказы
            pass  # Обновление должно происходить только по запросу через кнопку
        elif index == 2:  # Логи API
            self.load_api_logs_signal.emit()
        elif index == 3:  # Коды маркировки
            self.on_apply_marking_codes_filter()
        elif index == 4:  # Файлы агрегации
            self.load_aggregation_files_signal.emit()
    
    def create_status_bar(self):
        """Создание строки статуса с индикатором доступности API"""
        status_bar = self.statusBar()
        
        # Индикатор API
        self.api_status_label = QLabel("API: ")
        self.api_indicator = QLabel("⚪ Неизвестно")
        self.api_indicator.setMinimumWidth(150)
        
        # Индикатор активного сервера
        self.server_status_label = QLabel("Сервер: ")
        self.server_indicator = QLabel("Не выбран")
        self.server_indicator.setMinimumWidth(250)
        
        status_bar.addWidget(self.api_status_label)
        status_bar.addWidget(self.api_indicator)
        status_bar.addWidget(self.server_status_label)
        status_bar.addWidget(self.server_indicator)
        status_bar.addPermanentWidget(QLabel(""))  # Разделитель
    
    def update_api_status(self, is_available):
        """Обновление индикатора статуса API"""
        if is_available:
            self.api_indicator.setText("🟢 Доступен")
            self.api_indicator.setStyleSheet("color: green;")
        else:
            self.api_indicator.setText("🔴 Недоступен")
            self.api_indicator.setStyleSheet("color: red;")
    
    def update_server_status(self, server_name, server_url):
        """Обновление информации об активном сервере в строке состояния
        
        Args:
            server_name (str): Название сервера
            server_url (str): URL сервера
        """
        if server_name and server_url:
            self.server_indicator.setText(f"{server_name} ({server_url})")
            self.server_indicator.setToolTip(f"Название: {server_name}\nURL: {server_url}")
        else:
            self.server_indicator.setText("Не выбран")
            self.server_indicator.setToolTip("Активный сервер не выбран")
    
    def create_api_logs_tab(self):
        """Создание вкладки логов API"""
        self.api_logs_tab = QWidget()
        layout = QVBoxLayout(self.api_logs_tab)
        
        # Добавляем фильтры сверху
        filters_layout = QHBoxLayout()
        
        # Фильтр по HTTP-методам (GET, POST, PUT, DELETE)
        http_method_label = QLabel("HTTP-метод:")
        self.http_method_filter = QComboBox()
        self.http_method_filter.addItem("Все", "")
        self.http_method_filter.addItem("GET", "GET")
        self.http_method_filter.addItem("POST", "POST")
        self.http_method_filter.addItem("PUT", "PUT")
        self.http_method_filter.addItem("DELETE", "DELETE")
        filters_layout.addWidget(http_method_label)
        filters_layout.addWidget(self.http_method_filter)
        
        # Фильтр по API методам (ping, codes, utilisation и т.д.)
        api_method_label = QLabel("API метод:")
        self.api_method_filter = QComboBox()
        self.api_method_filter.addItem("Все", "")
        # Добавляем часто используемые методы API
        api_methods = ["ping", "codes", "utilisation", "orders", "aggregation", "report", "version"]
        for method in api_methods:
            self.api_method_filter.addItem(method, method)
        self.api_method_filter.setEditable(True)  # Позволяем вводить свои значения
        filters_layout.addWidget(api_method_label)
        filters_layout.addWidget(self.api_method_filter)
        
        # Кнопка применения фильтров
        apply_filters_button = QPushButton("Применить фильтры")
        apply_filters_button.clicked.connect(self.apply_api_logs_filters)
        filters_layout.addWidget(apply_filters_button)
        
        # Кнопка сброса фильтров
        reset_filters_button = QPushButton("Сбросить фильтры")
        reset_filters_button.clicked.connect(self.reset_api_logs_filters)
        filters_layout.addWidget(reset_filters_button)
        
        # Добавляем слой с фильтрами в основной слой
        layout.addLayout(filters_layout)
        
        # Создаем два виджета - для таблицы логов и просмотра деталей
        splitter = QSplitter(Qt.Orientation.Vertical)
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Таблица логов API
        self.api_logs_table = QTableWidget()
        self.api_logs_table.setColumnCount(7)
        self.api_logs_table.setHorizontalHeaderLabels(["ID", "Метод", "URL", "Код", "Успех", "Время", "Описание"])
        self.api_logs_table.itemSelectionChanged.connect(self.on_api_log_selected)
        logs_layout.addWidget(self.api_logs_table)
        
        # Кнопки для управления логами API
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить логи")
        refresh_button.clicked.connect(self.on_refresh_api_logs)
        buttons_layout.addWidget(refresh_button)
        
        export_descriptions_button = QPushButton("Экспорт описаний API")
        export_descriptions_button.clicked.connect(self.export_api_descriptions_signal.emit)
        buttons_layout.addWidget(export_descriptions_button)
        
        logs_layout.addLayout(buttons_layout)
        
        # Виджеты для просмотра деталей запроса и ответа
        details_layout.addWidget(QLabel("Детали запроса:"))
        self.request_details = QTextEdit()
        self.request_details.setReadOnly(True)
        details_layout.addWidget(self.request_details)
        
        details_layout.addWidget(QLabel("Детали ответа:"))
        self.response_details = QTextEdit()
        self.response_details.setReadOnly(True)
        details_layout.addWidget(self.response_details)
        
        # Добавляем виджеты в сплиттер
        splitter.addWidget(logs_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])
        
        # Добавляем сплиттер в макет вкладки
        layout.addWidget(splitter)
        
        # Храним полный список логов для фильтрации
        self.all_api_logs = []
    
    def on_refresh_api_logs(self):
        """Обработчик нажатия кнопки обновления логов API"""
        # Сбрасываем фильтры перед обновлением
        self.http_method_filter.setCurrentIndex(0)
        self.api_method_filter.setCurrentIndex(0)
        
        # Загружаем логи API
        self.load_api_logs_signal.emit()
    
    def apply_api_logs_filters(self):
        """Применение фильтров к таблице логов API"""
        if not hasattr(self, 'all_api_logs') or not self.all_api_logs:
            return
        
        # Получаем значения фильтров
        http_method = self.http_method_filter.currentData()
        api_method = self.api_method_filter.currentText().strip().lower()
        
        # Применяем фильтры
        filtered_logs = []
        for log in self.all_api_logs:
            # Фильтр по HTTP-методу
            if http_method and log["method"] != http_method:
                continue
                
            # Фильтр по API методу (проверяем наличие в URL)
            if api_method and api_method not in log["url"].lower():
                continue
                
            # Если прошли все фильтры, добавляем лог в отфильтрованный список
            filtered_logs.append(log)
        
        # Обновляем таблицу с отфильтрованными логами
        self._update_api_logs_table_with_data(filtered_logs)
        
        # Обновляем заголовок вкладки с количеством отображаемых логов
        tab_index = self.tabs.indexOf(self.api_logs_tab)
        if tab_index >= 0:
            self.tabs.setTabText(tab_index, f"Логи API ({len(filtered_logs)})")
    
    def reset_api_logs_filters(self):
        """Сброс фильтров логов API"""
        self.http_method_filter.setCurrentIndex(0)
        self.api_method_filter.setCurrentIndex(0)
        
        # Обновляем таблицу с полным списком логов
        self._update_api_logs_table_with_data(self.all_api_logs)
        
        # Обновляем заголовок вкладки
        tab_index = self.tabs.indexOf(self.api_logs_tab)
        if tab_index >= 0:
            self.tabs.setTabText(tab_index, f"Логи API ({len(self.all_api_logs)})")
    
    def on_api_log_selected(self):
        """Обработчик выбора лога API в таблице"""
        selected_rows = self.api_logs_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            log_id = int(self.api_logs_table.item(row, 0).text())
            
            # Используем сигнал для получения деталей лога API
            # Передаем callback функции для обработки результата
            self.get_api_log_details_signal.emit(
                log_id, 
                lambda data: self.update_request_details(data), 
                lambda data: self.update_response_details(data)
            )
    
    def update_request_details(self, request_json):
        """Обновление деталей запроса"""
        try:
            request_data = json.loads(request_json)
            
            # Форматирование запроса
            request_formatted = ""
            if 'headers' in request_data and request_data['headers']:
                request_formatted += "Заголовки запроса:\n"
                for header, value in request_data['headers'].items():
                    request_formatted += f"{header}: {value}\n"
            
            if 'data' in request_data and request_data['data']:
                request_formatted += "\nДанные запроса:\n"
                request_formatted += json.dumps(request_data['data'], ensure_ascii=False, indent=4)
            
            # Устанавливаем текст в многострочное текстовое поле
            self.request_details.setPlainText(request_formatted)
            
        except Exception as e:
            error_message = f"Ошибка форматирования запроса: {str(e)}"
            print(error_message)
            self.request_details.setPlainText(f"{error_message}\n\nИсходные данные:\n{request_json}")
    
    def update_response_details(self, response_json):
        """Обновление деталей ответа"""
        try:
            response_data = json.loads(response_json)
            
            # Форматирование ответа
            response_formatted = json.dumps(response_data, ensure_ascii=False, indent=4)
            
            # Устанавливаем текст в многострочное текстовое поле
            self.response_details.setPlainText(response_formatted)
            
        except Exception as e:
            error_message = f"Ошибка форматирования ответа: {str(e)}"
            print(error_message)
            self.response_details.setPlainText(f"{error_message}\n\nИсходные данные:\n{response_json}")
    
    def update_api_logs_table(self, logs):
        """Обновление таблицы логов API"""
        # Сохраняем полный список логов для фильтрации
        self.all_api_logs = logs
        
        # Обновляем таблицу
        self._update_api_logs_table_with_data(logs)
        
        # Обновляем заголовок вкладки с количеством логов
        tab_index = self.tabs.indexOf(self.api_logs_tab)
        if tab_index >= 0:
            self.tabs.setTabText(tab_index, f"Логи API ({len(logs)})")
            
        # Обновляем список API методов в фильтре на основе загруженных логов
        self.update_api_method_filter_items(logs)
    
    def _update_api_logs_table_with_data(self, logs):
        """Обновление таблицы логов API конкретными данными"""
        # Настраиваем таблицу для хранения всех данных
        self.api_logs_table.setColumnCount(9)
        self.api_logs_table.setHorizontalHeaderLabels(["ID", "Метод", "URL", "Код", "Успех", "Время", "Описание", "request_data", "response_data"])
        
        self.api_logs_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.api_logs_table.setItem(row, 0, QTableWidgetItem(str(log["id"])))
            self.api_logs_table.setItem(row, 1, QTableWidgetItem(log["method"]))
            self.api_logs_table.setItem(row, 2, QTableWidgetItem(log["url"]))
            self.api_logs_table.setItem(row, 3, QTableWidgetItem(str(log["status_code"])))
            
            # Индикатор успеха
            success_item = QTableWidgetItem("✓" if log["success"] else "✗")
            success_item.setBackground(QColor(200, 255, 200) if log["success"] else QColor(255, 200, 200))
            self.api_logs_table.setItem(row, 4, success_item)
            
            # Форматируем время
            timestamp = datetime.datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            self.api_logs_table.setItem(row, 5, QTableWidgetItem(formatted_time))
            
            # Добавляем описание запроса, если оно есть
            description = log.get("description", "")
            self.api_logs_table.setItem(row, 6, QTableWidgetItem(description))
            
            # Сохраняем запрос и ответ в скрытых ячейках
            self.api_logs_table.setItem(row, 7, QTableWidgetItem(log["request"]))
            self.api_logs_table.setItem(row, 8, QTableWidgetItem(log["response"]))
        
        # Скрываем колонки с данными запроса и ответа
        self.api_logs_table.setColumnHidden(7, True)
        self.api_logs_table.setColumnHidden(8, True)
        
        # Подгоняем размеры колонок
        self.api_logs_table.resizeColumnsToContents()
    
    def update_api_method_filter_items(self, logs):
        """Обновляет список доступных API методов на основе загруженных логов"""
        # Сохраняем текущий выбранный элемент
        current_text = self.api_method_filter.currentText()
        
        # Получаем уникальные API методы из логов
        api_methods = set()
        
        # Известные API методы, которые можно встретить в URL
        known_api_methods = [
            "ping", "codes", "utilisation", "orders", "aggregation", "report", "version", 
            "status", "buffers", "emission", "authentication", "token", "certificates", 
            "nomenclature", "registration", "documents", "quota", "pool"
        ]
        
        for log in logs:
            # Извлекаем из URL имя метода API
            url = log["url"].lower()
            
            # Создаем более продвинутый алгоритм извлечения метода API из URL
            # Сначала проверяем, есть ли в URL путь /api/v*/ для определения API запросов
            if "/api/v" in url:
                # Разбиваем URL на части и анализируем
                parts = url.split('/')
                for i, part in enumerate(parts):
                    # Пропускаем пустые строки и общие элементы URL
                    if not part or part in ["api", "v1", "v2", "v3", "pharma", "tobacco", "shoes"]:
                        continue
                    
                    # Проверяем, есть ли часть в списке известных методов API
                    if part in known_api_methods:
                        api_methods.add(part)
                    # Проверяем на наличие параметров (часть может содержать ? или &)
                    elif "?" in part:
                        clean_part = part.split("?")[0]
                        if clean_part and clean_part in known_api_methods:
                            api_methods.add(clean_part)
                    # Если часть содержит цифры, это может быть ID ресурса, проверяем предыдущую часть
                    elif part.isdigit() and i > 0 and parts[i-1] in known_api_methods:
                        api_methods.add(parts[i-1])
            
            # Проверяем URL по описанию лога, если там указан метод API
            description = log.get("description", "").lower()
            for method in known_api_methods:
                if method in description:
                    api_methods.add(method)
        
        # Если методы не были найдены по URL, используем анализ описаний логов
        if not api_methods:
            for log in logs:
                description = log.get("description", "").lower()
                
                # Часто в описании указывается действие, например "Получение статуса заказов"
                action_mapping = {
                    "получение заказов": "orders",
                    "получение статуса заказов": "status",
                    "проверка доступности": "ping",
                    "получение кодов": "codes",
                    "отчет о нанесении": "utilisation",
                    "получение агрегации": "aggregation",
                    "получение отчета": "report",
                    "получение версии": "version",
                    "эмиссия": "emission",
                    "аутентификация": "authentication",
                    "регистрация": "registration"
                }
                
                for action, method in action_mapping.items():
                    if action in description:
                        api_methods.add(method)
        
        # Очищаем список методов и добавляем "Все"
        self.api_method_filter.clear()
        self.api_method_filter.addItem("Все", "")
        
        # Добавляем найденные методы
        for method in sorted(api_methods):
            self.api_method_filter.addItem(method, method)
        
        # Если методы вообще не обнаружены, добавляем стандартный набор
        if not api_methods:
            for method in ["ping", "codes", "utilisation", "orders", "aggregation", "report", "version"]:
                self.api_method_filter.addItem(method, method)
        
        # Восстанавливаем выбранный элемент, если он есть в списке
        index = self.api_method_filter.findText(current_text)
        if index >= 0:
            self.api_method_filter.setCurrentIndex(index)
        else:
            self.api_method_filter.setCurrentIndex(0)  # Устанавливаем "Все"
    
    def create_extensions_tab(self):
        """Создание вкладки расширений API"""
        self.extensions_tab = QWidget()
        layout = QVBoxLayout(self.extensions_tab)
        
        # Таблица расширений API
        self.extensions_table = QTableWidget()
        self.extensions_table.setColumnCount(4)
        self.extensions_table.setHorizontalHeaderLabels(["ID", "Название", "Код", "Активный"])
        layout.addWidget(self.extensions_table)
        
        # Кнопки управления расширениями API
        buttons_layout = QHBoxLayout()
        
        set_active_button = QPushButton("Установить активным")
        set_active_button.clicked.connect(self.on_set_active_extension)
        buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(buttons_layout)
    
    def on_set_active_extension(self):
        """Обработчик нажатия кнопки установки активного расширения API"""
        row = self.extensions_table.currentRow()
        if row >= 0:
            extension_id = int(self.extensions_table.item(row, 0).text())
            self.set_active_extension_signal.emit(extension_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите вид продукции для активации")
    
    def update_extensions_table(self, extensions):
        """Обновление таблицы расширений API"""
        self.extensions_table.setRowCount(len(extensions))
        for row, extension in enumerate(extensions):
            self.extensions_table.setItem(row, 0, QTableWidgetItem(str(extension.id)))
            self.extensions_table.setItem(row, 1, QTableWidgetItem(extension.name))
            self.extensions_table.setItem(row, 2, QTableWidgetItem(extension.code))
            self.extensions_table.setItem(row, 3, QTableWidgetItem("Да" if extension.is_active else "Нет"))
    
    def on_add_order_clicked(self):
        """Обработчик нажатия на кнопку добавления заказа"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
        
        # Запрашиваем номер заказа через диалоговое окно
        order_number, ok = QInputDialog.getText(
            self, "Добавление заказа", "Введите номер заказа:", QLineEdit.EchoMode.Normal
        )
        
        if ok and order_number:
            # Запрашиваем статус заказа
            status, ok = QInputDialog.getText(
                self, "Добавление заказа", "Введите статус заказа:", QLineEdit.EchoMode.Normal
            )
            
            if ok and status:
                # Вызываем сигнал добавления заказа
                self.add_order_signal.emit(order_number, status)
            else:
                QMessageBox.warning(self, "Предупреждение", "Статус заказа не указан")
        else:
            QMessageBox.warning(self, "Предупреждение", "Номер заказа не указан")
    
    def on_ping_clicked(self):
        """Обработчик нажатия кнопки проверки API"""
        self.ping_signal.emit()
    
    def on_get_orders_clicked(self):
        """Обработчик нажатия кнопки получения заказов"""
        self.get_orders_signal.emit()
    
    def on_get_report_clicked(self):
        """Обработчик нажатия кнопки получения отчета"""
        self.get_report_signal.emit()
    
    def on_get_version_clicked(self):
        """Обработчик нажатия кнопки получения версии СУЗ и API"""
        self.get_version_signal.emit()
    
    def on_get_orders_status_clicked(self):
        """Обработчик нажатия кнопки получения статуса заказов"""
        self.get_orders_status_signal.emit()
    
    def on_add_connection_clicked(self):
        """Обработчик нажатия кнопки добавления подключения"""
        dialog = ConnectionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.add_connection_signal.emit(data['name'], data['url'])
    
    def on_edit_connection_clicked(self):
        """Обработчик нажатия кнопки редактирования подключения"""
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            name = self.connections_table.item(row, 1).text()
            url = self.connections_table.item(row, 2).text()
            
            dialog = ConnectionDialog(self)
            # Заполняем поля текущими значениями
            dialog.name_input.setText(name)
            dialog.url_input.setText(url)
            
            if dialog.exec():
                data = dialog.get_data()
                self.edit_connection_signal.emit(connection_id, data['name'], data['url'])
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для редактирования")
    
    def on_delete_connection_clicked(self):
        """Обработчик нажатия кнопки удаления подключения"""
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            self.delete_connection_signal.emit(connection_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для удаления")
    
    def on_set_active_connection_clicked(self):
        """Обработчик нажатия кнопки установки активного подключения"""
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            self.set_active_connection_signal.emit(connection_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для активации")
    
    def on_add_credentials_clicked(self):
        """Обработчик нажатия кнопки добавления учетных данных"""
        dialog = CredentialsDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            
            # Получаем выбранное подключение, если оно есть
            connection_id = None
            row = self.connections_table.currentRow()
            if row >= 0:
                connection_id = int(self.connections_table.item(row, 0).text())
            
            # Теперь connection_id необязательный параметр
            self.add_credentials_signal.emit(data['omsid'], data['token'], data['gln'], connection_id)
    
    def on_edit_credentials_clicked(self):
        """Обработчик нажатия кнопки редактирования учетных данных"""
        selected_rows = self.credentials_table.selectedItems()
        if not selected_rows:
            self.show_message("Предупреждение", "Выберите учетные данные для редактирования")
            return
        
        row = selected_rows[0].row()
        
        # Получаем данные из таблицы
        try:
            credentials_id = int(self.credentials_table.item(row, 0).text()) if self.credentials_table.item(row, 0) else 0
            omsid = self.credentials_table.item(row, 1).text() if self.credentials_table.item(row, 1) else ""
            token = self.credentials_table.item(row, 2).text() if self.credentials_table.item(row, 2) else ""
            gln = self.credentials_table.item(row, 3).text() if self.credentials_table.item(row, 3) else ""
            
            # Открываем диалог редактирования
            dialog = CredentialsDialog(self, {"omsid": omsid, "token": token, "gln": gln})
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                self.edit_credentials_signal.emit(credentials_id, data['omsid'], data['token'], data['gln'])
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при редактировании учетных данных: {str(e)}")
    
    def on_delete_credentials_clicked(self):
        """Обработчик нажатия кнопки удаления учетных данных"""
        selected_rows = self.credentials_table.selectedItems()
        if not selected_rows:
            self.show_message("Предупреждение", "Выберите учетные данные для удаления")
            return
        
        row = selected_rows[0].row()
        
        try:
            # Получаем ID учетных данных
            credentials_id = int(self.credentials_table.item(row, 0).text()) if self.credentials_table.item(row, 0) else 0
            
            # Запрашиваем подтверждение
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setText("Вы уверены, что хотите удалить эти учетные данные?")
            msg_box.setWindowTitle("Подтверждение удаления")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                # Вызываем сигнал удаления учетных данных
                self.delete_credentials_signal.emit(credentials_id)
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при удалении учетных данных: {str(e)}")
    
    def on_add_nomenclature_clicked(self):
        """Обработчик нажатия кнопки добавления номенклатуры"""
        # Получаем список расширений API
        extensions = []
        source_table = self.main_window.extensions_table
        for row in range(source_table.rowCount()):
            extension_id = int(source_table.item(row, 0).text())
            extension_name = source_table.item(row, 1).text()
            extension_code = source_table.item(row, 2).text()
            is_active = source_table.item(row, 3).text() == "Да"
            extensions.append(Extension(extension_id, extension_code, extension_name, is_active))
        
        dialog = NomenclatureDialog(self, extensions=extensions)
        if dialog.exec():
            data = dialog.get_data()
            self.add_nomenclature_signal.emit(data['name'], data['gtin'], data['product_group'])
    
    def on_edit_nomenclature_clicked(self):
        """Обработчик нажатия кнопки редактирования номенклатуры"""
        row = self.nomenclature_table.currentRow()
        if row >= 0:
            nomenclature_id = int(self.nomenclature_table.item(row, 0).text())
            name = self.nomenclature_table.item(row, 1).text()
            gtin = self.nomenclature_table.item(row, 2).text()
            product_group = self.nomenclature_table.item(row, 3).text() if self.nomenclature_table.item(row, 3) else ""
            
            # Создаем объект номенклатуры
            nomenclature = Nomenclature(nomenclature_id, name, gtin, product_group)
            
            # Получаем список расширений API перед открытием диалога
            extensions = []
            source_table = self.main_window.extensions_table
            for row in range(source_table.rowCount()):
                extension_id = int(source_table.item(row, 0).text())
                extension_name = source_table.item(row, 1).text()
                extension_code = source_table.item(row, 2).text()
                is_active = source_table.item(row, 3).text() == "Да"
                extensions.append(Extension(extension_id, extension_code, extension_name, is_active))
            
            # Открываем диалог редактирования
            dialog = NomenclatureDialog(self, nomenclature=nomenclature, extensions=extensions)
            if dialog.exec():
                data = dialog.get_data()
                self.edit_nomenclature_signal.emit(nomenclature_id, data['name'], data['gtin'], data['product_group'])
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите номенклатуру для редактирования")
    
    def on_delete_nomenclature_clicked(self):
        """Обработчик нажатия кнопки удаления номенклатуры"""
        row = self.nomenclature_table.currentRow()
        if row >= 0:
            nomenclature_id = int(self.nomenclature_table.item(row, 0).text())
            self.main_window.delete_nomenclature_signal.emit(nomenclature_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите номенклатуру для удаления")
    
    def update_orders_table(self, orders):
        """Обновление таблицы заказов"""
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(row, 1, QTableWidgetItem(str(order.order_number)))
            
            # Статус заказа с цветовым выделением
            status_item = QTableWidgetItem(order.status)
            if order.status == "Принят":
                status_item.setBackground(QColor(200, 255, 200))  # Зеленый для принятых заказов
            elif order.status == "Непринят":
                status_item.setBackground(QColor(255, 200, 200))  # Красный для непринятых заказов
            self.orders_table.setItem(row, 2, status_item)
            
            # Дата создания
            self.orders_table.setItem(row, 3, QTableWidgetItem(str(order.timestamp)))
            
            # Описание с ожидаемым временем выполнения
            description = ""
            if hasattr(order, 'expected_complete') and order.expected_complete:
                description = f"Ожидаемое время выполнения: {order.expected_complete}"
            elif hasattr(order, 'description') and order.description:
                description = order.description
            self.orders_table.setItem(row, 4, QTableWidgetItem(description))
        
        # Подгоняем размеры колонок
        self.orders_table.resizeColumnsToContents()
    
    def update_connections_table(self, connections):
        """Обновление таблицы подключений"""
        self.connections_table.setRowCount(len(connections))
        for row, connection in enumerate(connections):
            self.connections_table.setItem(row, 0, QTableWidgetItem(str(connection.id)))
            self.connections_table.setItem(row, 1, QTableWidgetItem(connection.name))
            self.connections_table.setItem(row, 2, QTableWidgetItem(connection.url))
            self.connections_table.setItem(row, 3, QTableWidgetItem("Да" if connection.is_active else "Нет"))
    
    def update_credentials_table(self, credentials):
        """Обновление таблицы учетных данных"""
        self.credentials_table.setRowCount(len(credentials))
        for row, cred in enumerate(credentials):
            self.credentials_table.setItem(row, 0, QTableWidgetItem(str(cred.id)))
            self.credentials_table.setItem(row, 1, QTableWidgetItem(cred.omsid))
            self.credentials_table.setItem(row, 2, QTableWidgetItem(cred.token))
            self.credentials_table.setItem(row, 3, QTableWidgetItem(cred.gln))
    
    def update_nomenclature_table(self, nomenclature):
        """Обновление таблицы номенклатуры"""
        self.nomenclature_table.setRowCount(len(nomenclature))
        for row, item in enumerate(nomenclature):
            self.nomenclature_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.nomenclature_table.setItem(row, 1, QTableWidgetItem(item.name))
            self.nomenclature_table.setItem(row, 2, QTableWidgetItem(item.gtin))
            self.nomenclature_table.setItem(row, 3, QTableWidgetItem(item.product_group))
    
    def update_countries_table(self, countries):
        """Обновление таблицы стран"""
        self.countries_table.setRowCount(len(countries))
        for row, country in enumerate(countries):
            self.countries_table.setItem(row, 0, QTableWidgetItem(str(country.id)))
            self.countries_table.setItem(row, 1, QTableWidgetItem(country.code))
            self.countries_table.setItem(row, 2, QTableWidgetItem(country.name))
        self.countries_table.resizeColumnsToContents()
    
    def show_message(self, title, message):
        """Показать сообщение"""
        QMessageBox.information(self, title, message)

    def create_orders_tab(self):
        """Создание вкладки заказов"""
        self.orders_tab = QWidget()
        layout = QVBoxLayout(self.orders_tab)
        
        # Создаем сплиттер для разделения списка заказов и деталей заказа
        splitter = QSplitter(Qt.Orientation.Vertical)
        orders_widget = QWidget()
        orders_layout = QVBoxLayout(orders_widget)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Верхняя часть: таблица заказов и кнопки управления
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Номер", "Статус", "Дата создания", "Описание"])
        self.orders_table.itemSelectionChanged.connect(self.on_order_selected)
        orders_layout.addWidget(self.orders_table)
        
        # Кнопки управления заказами
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить заказ")
        add_button.clicked.connect(self.on_add_order_clicked)
        buttons_layout.addWidget(add_button)
        
        ping_button = QPushButton("Проверить доступность API")
        ping_button.clicked.connect(self.on_ping_clicked)
        buttons_layout.addWidget(ping_button)
        
        get_orders_button = QPushButton("Получить заказы")
        get_orders_button.clicked.connect(self.on_get_orders_clicked)
        buttons_layout.addWidget(get_orders_button)
        
        get_report_button = QPushButton("Получить отчет")
        get_report_button.clicked.connect(self.on_get_report_clicked)
        buttons_layout.addWidget(get_report_button)
        
        get_version_button = QPushButton("Получить версию")
        get_version_button.clicked.connect(self.on_get_version_clicked)
        buttons_layout.addWidget(get_version_button)
        
        get_orders_status_button = QPushButton("Получить статусы заказов")
        get_orders_status_button.clicked.connect(self.on_get_orders_status_clicked)
        buttons_layout.addWidget(get_orders_status_button)
        
        create_emission_order_button = QPushButton("Создать заказ на эмиссию")
        create_emission_order_button.clicked.connect(self.on_create_emission_order_clicked)
        buttons_layout.addWidget(create_emission_order_button)
        
        orders_layout.addLayout(buttons_layout)
        
        # Нижняя часть: детали заказа
        details_layout.addWidget(QLabel("Детали заказа:"))
        self.order_details_table = QTableWidget()
        self.order_details_table.setColumnCount(3)
        self.order_details_table.setHorizontalHeaderLabels(["GTIN", "Количество", "Статус"])
        details_layout.addWidget(self.order_details_table)
        
        # Добавляем виджеты в сплиттер
        splitter.addWidget(orders_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])
        
        # Добавляем сплиттер в макет вкладки
        layout.addWidget(splitter)
    
    def on_order_selected(self):
        """Обработчик выбора заказа в таблице"""
        selected_rows = self.orders_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            order_id = int(self.orders_table.item(row, 0).text())
            # Эмитируем сигнал для получения деталей заказа
            self.get_order_details_signal.emit(str(order_id))
    
    def update_order_details_table(self, products):
        """Обновление таблицы деталей заказа"""
        self.order_details_table.setRowCount(len(products))
        for row, product in enumerate(products):
            # Получаем название продукта или используем GTIN, если название не найдено
            product_name = product.get("product_name", "") or product.get("gtin", "")
            self.order_details_table.setItem(row, 0, QTableWidgetItem(product_name))
            self.order_details_table.setItem(row, 1, QTableWidgetItem(str(product.get("quantity", ""))))
        
        # Подгоняем размеры колонок
        self.order_details_table.resizeColumnsToContents()
    
    def on_create_emission_order_clicked(self):
        """Обработчик нажатия кнопки создания заказа на эмиссию КМ"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from views.dialogs import EmissionOrderDialog
        from models.models import EmissionType
        
        # Получаем данные в контроллере через сигналы и слоты
        # В MainWindow нет прямого доступа к self.controller
        # Получаем данные для диалога через вызов соответствующих сигналов
        self.load_api_logs_signal.emit()  # Обновляем логи чтобы получить актуальную информацию
        
        # Получаем данные напрямую из виджетов, так как у нас нет прямого доступа к БД
        nomenclatures = []
        extensions = []
        countries = []
        
        # Получаем данные о номенклатуре из таблицы
        for row in range(self.nomenclature_table.rowCount()):
            id_item = self.nomenclature_table.item(row, 0)
            name_item = self.nomenclature_table.item(row, 1)
            gtin_item = self.nomenclature_table.item(row, 2)
            group_item = self.nomenclature_table.item(row, 3)
            
            if id_item and name_item and gtin_item:
                from models.models import Nomenclature
                nomenclature = Nomenclature(
                    int(id_item.text()),
                    name_item.text(),
                    gtin_item.text(),
                    group_item.text() if group_item else ""
                )
                nomenclatures.append(nomenclature)
        
        # Получаем данные о расширениях API из таблицы
        for row in range(self.extensions_table.rowCount()):
            id_item = self.extensions_table.item(row, 0)
            name_item = self.extensions_table.item(row, 1)
            is_active_item = self.extensions_table.item(row, 3)
            
            if id_item and name_item and is_active_item:
                from models.models import Extension
                extension = Extension(
                    int(id_item.text()),
                    name_item.text() if hasattr(name_item, 'text') else "",
                    name_item.text() if hasattr(name_item, 'text') else "",
                    is_active_item.text() == "Да" if hasattr(is_active_item, 'text') else False
                )
                extensions.append(extension)
        
        # Получаем данные о странах из таблицы
        for row in range(self.countries_table.rowCount()):
            id_item = self.countries_table.item(row, 0)
            code_item = self.countries_table.item(row, 1)
            name_item = self.countries_table.item(row, 2)
            
            if id_item and code_item and name_item:
                from models.models import Country
                country = Country(
                    int(id_item.text()),
                    code_item.text(),
                    name_item.text()
                )
                countries.append(country)
        
        # Добавим страны по умолчанию, если таблица пуста
        if not countries:
            from models.models import Country
            default_countries = [
                Country(1, "BY", "Беларусь"),
                Country(2, "RU", "Россия"),
                Country(3, "KZ", "Казахстан")
            ]
            countries.extend(default_countries)
            
        # Получаем данные о типах эмиссии из контроллера
        # Но поскольку нет прямого доступа к базе данных, создаем типы эмиссии вручную
        emission_types = [
            EmissionType(1, "PRODUCTION", "Производство в Казахстане", None),
            EmissionType(2, "IMPORT", "Ввезен в Казахстан (Импорт)", None),
            EmissionType(3, "REMAINS", "Маркировка остатков", "shoes"),
            EmissionType(4, "COMMISSION", "Принят на коммиссию от физ.лица", "shoes"),
            EmissionType(5, "REMARK", "Перемаркировка", None)
        ]
        
        # Если нет расширений, добавляем стандартные
        if not extensions:
            from models.models import Extension
            default_extensions = [
                Extension(1, "pharma", "Фармацевтическая продукция", True),
                Extension(2, "tobacco", "Табачная продукция", False),
                Extension(3, "shoes", "Обувь", False),
                Extension(4, "tires", "Шины", False),
                Extension(5, "lp", "Легкая промышленность", False),
                Extension(6, "perfum", "Парфюмерия", False),
                Extension(7, "photo", "Фототехника", False),
                Extension(8, "milk", "Молочная продукция", False),
                Extension(9, "water", "Упакованная вода", False)
            ]
            extensions.extend(default_extensions)
        
        # Создаем диалог с передачей всех данных
        dialog = EmissionOrderDialog(self, nomenclatures, extensions, emission_types, countries)
        if dialog.exec():
            # Получаем данные заказа из диалога
            order_data = dialog.get_data()
            # Отправляем сигнал с данными заказа
            self.create_emission_order_signal.emit(order_data)

    def create_countries_tab(self):
        """Создание вкладки стран"""
        self.countries_tab = QWidget()
        layout = QVBoxLayout(self.countries_tab)
        
        # Таблица стран
        self.countries_table = QTableWidget()
        self.countries_table.setColumnCount(3)
        self.countries_table.setHorizontalHeaderLabels(["ID", "Код", "Название"])
        layout.addWidget(self.countries_table)
        
        # В этой вкладке обычно нет кнопок управления, так как
        # список стран обычно загружается из API и не редактируется пользователем
    
    def create_order_statuses_tab(self):
        """Создание вкладки статусов заказов"""
        self.order_statuses_tab = QWidget()
        layout = QVBoxLayout(self.order_statuses_tab)
        
        # Таблица статусов заказов
        self.order_statuses_table = QTableWidget()
        self.order_statuses_table.setColumnCount(4)
        self.order_statuses_table.setHorizontalHeaderLabels(["ID", "Код", "Название", "Описание"])
        layout.addWidget(self.order_statuses_table)
        
        # Кнопки управления статусами
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(lambda: self.main_window.load_order_statuses_signal.emit())
        buttons_layout.addWidget(refresh_button)
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_order_status_clicked)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_order_status_clicked)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_order_status_clicked)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
        
    def reload_countries(self, *args):
        """Обновить таблицу стран в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.countries_table
        self.countries_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.countries_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.countries_table.resizeColumnsToContents()
    
    def reload_nomenclature(self, *args):
        """Обновить таблицу номенклатуры в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.nomenclature_table
        self.nomenclature_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.nomenclature_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.nomenclature_table.resizeColumnsToContents()
    
    def reload_order_statuses(self, *args):
        """Обновить таблицу статусов заказов в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.order_statuses_table
        self.order_statuses_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.order_statuses_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.order_statuses_table.resizeColumnsToContents()

    def show_catalogs_dialog(self):
        """Показать диалог справочников"""
        dialog = CatalogsDialog(self)
        dialog.exec()
    
    def show_settings_dialog(self):
        """Показать диалог настроек"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def create_connections_tab(self):
        """Создание вкладки подключений"""
        self.connections_tab = QWidget()
        layout = QVBoxLayout(self.connections_tab)
        
        # Таблица подключений
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(4)
        self.connections_table.setHorizontalHeaderLabels(["ID", "Название", "URL", "Активный"])
        layout.addWidget(self.connections_table)
        
        # Кнопки управления подключениями
        self.connections_buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_connection_clicked)
        self.connections_buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_connection_clicked)
        self.connections_buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_connection_clicked)
        self.connections_buttons_layout.addWidget(delete_button)
        
        set_active_button = QPushButton("Установить активным")
        set_active_button.clicked.connect(self.on_set_active_connection_clicked)
        self.connections_buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(self.connections_buttons_layout)

    def create_credentials_tab(self):
        """Создание вкладки учетных данных"""
        self.credentials_tab = QWidget()
        layout = QVBoxLayout(self.credentials_tab)
        
        # Таблица учетных данных
        self.credentials_table = QTableWidget()
        self.credentials_table.setColumnCount(4)
        self.credentials_table.setHorizontalHeaderLabels(["ID", "OMS ID", "Токен", "GLN"])
        layout.addWidget(self.credentials_table)
        
        # Кнопки управления учетными данными
        self.credentials_buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_credentials_clicked)
        self.credentials_buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_credentials_clicked)
        self.credentials_buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_credentials_clicked)
        self.credentials_buttons_layout.addWidget(delete_button)
        
        layout.addLayout(self.credentials_buttons_layout)

    def create_nomenclature_tab(self):
        """Создание вкладки номенклатуры"""
        self.nomenclature_tab = QWidget()
        layout = QVBoxLayout(self.nomenclature_tab)
        
        # Создаем копию таблицы номенклатуры и подключаем данные
        self.nomenclature_table = QTableWidget()
        self.nomenclature_table.setColumnCount(4)
        self.nomenclature_table.setHorizontalHeaderLabels(["ID", "Название", "GTIN", "Описание"])
        layout.addWidget(self.nomenclature_table)
        
        # Создаем кнопки для управления номенклатурой
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_nomenclature_clicked)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_nomenclature_clicked)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_nomenclature_clicked)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
    
    def on_add_order_status_clicked(self):
        """Обработчик нажатия кнопки добавления статуса заказа"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        # Запрашиваем код статуса
        code, ok = QInputDialog.getText(
            self, "Добавление статуса заказа", "Введите код статуса:", QLineEdit.EchoMode.Normal
        )
        
        if ok and code:
            # Запрашиваем название статуса
            name, ok = QInputDialog.getText(
                self, "Добавление статуса заказа", "Введите название статуса:", QLineEdit.EchoMode.Normal
            )
            
            if ok and name:
                # Запрашиваем описание статуса
                description, ok = QInputDialog.getText(
                    self, "Добавление статуса заказа", "Введите описание статуса:", QLineEdit.EchoMode.Normal
                )
                
                if ok:
                    # Вызываем сигнал добавления статуса напрямую из главного окна
                    # Важно: не self.main_window.add_order_status_signal.emit,
                    # а именно self.main_window.add_order_status_signal напрямую
                    self.main_window.add_order_status_signal.emit(code, name, description)
    
    def on_edit_order_status_clicked(self):
        """Обработчик нажатия кнопки редактирования статуса заказа"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        row = self.order_statuses_table.currentRow()
        if row >= 0:
            status_id = int(self.order_statuses_table.item(row, 0).text())
            code = self.order_statuses_table.item(row, 1).text()
            name = self.order_statuses_table.item(row, 2).text()
            description = self.order_statuses_table.item(row, 3).text() if self.order_statuses_table.item(row, 3) else ""
            
            # Запрашиваем новый код статуса
            new_code, ok = QInputDialog.getText(
                self, "Редактирование статуса заказа", "Введите код статуса:", QLineEdit.EchoMode.Normal, code
            )
            
            if ok and new_code:
                # Запрашиваем новое название статуса
                new_name, ok = QInputDialog.getText(
                    self, "Редактирование статуса заказа", "Введите название статуса:", QLineEdit.EchoMode.Normal, name
                )
                
                if ok and new_name:
                    # Запрашиваем новое описание статуса
                    new_description, ok = QInputDialog.getText(
                        self, "Редактирование статуса заказа", "Введите описание статуса:", QLineEdit.EchoMode.Normal, description
                    )
                    
                    if ok:
                        # Вызываем сигнал редактирования статуса из главного окна
                        self.main_window.edit_order_status_signal.emit(status_id, new_code, new_name, new_description)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите статус заказа для редактирования")
    
    def on_delete_order_status_clicked(self):
        """Обработчик нажатия кнопки удаления статуса заказа"""
        row = self.order_statuses_table.currentRow()
        if row >= 0:
            status_id = int(self.order_statuses_table.item(row, 0).text())
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, "Подтверждение удаления", 
                "Вы уверены, что хотите удалить этот статус заказа?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Вызываем сигнал удаления статуса из главного окна
                self.main_window.delete_order_status_signal.emit(status_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите статус заказа для удаления")

    def update_api_orders_table(self, order_infos):
        """Обновление таблицы API заказов
        
        Args:
            order_infos (List[Dict]): Список заказов из API
        """
        # Очищаем таблицу
        self.api_orders_table.setRowCount(0)
        
        # Обновляем количество столбцов
        self.api_orders_table.setColumnCount(10)
        self.api_orders_table.setHorizontalHeaderLabels([
            "ID заказа", "Статус", "Описание статуса", "Создан", "Количество", "Кол-во продуктов", 
            "Тип продукции", "Подписан", "Проверен", "Буферы"
        ])
        
        # Заполняем таблицу данными
        for i, order_info in enumerate(order_infos):
            self.api_orders_table.insertRow(i)
            
            # Проверяем, является ли заказ устаревшим
            is_obsolete = order_info.get("orderStatus", "") == "OBSOLETE"
            
            # Заполняем ячейки таблицы
            self.api_orders_table.setItem(i, 0, QTableWidgetItem(str(order_info.get("orderId", ""))))
            
            # Статус заказа - специальное форматирование для устаревших
            status_item = QTableWidgetItem(str(order_info.get("orderStatus", "")))
            if is_obsolete:
                status_item.setBackground(QColor(255, 200, 200))  # Светло-красный цвет
            self.api_orders_table.setItem(i, 1, status_item)
            
            # Описание статуса
            self.api_orders_table.setItem(i, 2, QTableWidgetItem(str(order_info.get("orderStatusDescription", ""))))
            
            # Остальные поля
            self.api_orders_table.setItem(i, 3, QTableWidgetItem(str(order_info.get("createdTimestamp", ""))))
            self.api_orders_table.setItem(i, 4, QTableWidgetItem(str(order_info.get("totalQuantity", 0))))
            self.api_orders_table.setItem(i, 5, QTableWidgetItem(str(order_info.get("numOfProducts", 0))))
            self.api_orders_table.setItem(i, 6, QTableWidgetItem(str(order_info.get("productGroupType", ""))))
            self.api_orders_table.setItem(i, 7, QTableWidgetItem(str(order_info.get("signed", False))))
            self.api_orders_table.setItem(i, 8, QTableWidgetItem(str(order_info.get("verified", False))))
            
            # Если есть буферы, добавляем их в последний столбец
            buffers = order_info.get("buffers", [])
            buffers_text = str(len(buffers)) if buffers else "0"
            self.api_orders_table.setItem(i, 9, QTableWidgetItem(buffers_text))
            
            # Для устаревших заказов делаем строку серой
            if is_obsolete:
                for col in range(self.api_orders_table.columnCount()):
                    item = self.api_orders_table.item(i, col)
                    if item:
                        item.setForeground(QColor(128, 128, 128))  # Серый цвет
        
        # Подгоняем размеры колонок
        self.api_orders_table.resizeColumnsToContents()
    
    def set_api_orders_status(self, status_message):
        """Отображение статуса API заказов в строке состояния
        
        Args:
            status_message (str): Сообщение о статусе API заказов
        """
        # Проверяем, существует ли label для статуса API заказов
        if hasattr(self, 'api_orders_status_label'):
            self.api_orders_status_label.setText(status_message)
        else:
            # Если нет, создаем новый label и проверяем, существует ли api_orders_tab_layout
            self.api_orders_status_label = QLabel(status_message)
            self.api_orders_status_label.setStyleSheet("color: #333; font-size: 11px;")
            if hasattr(self, 'api_orders_tab_layout'):
                self.api_orders_tab_layout.addWidget(self.api_orders_status_label)

    def on_delete_api_order_clicked(self):
        """Обработчик нажатия кнопки удаления API заказа"""
        selected_rows = self.api_orders_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            order_id = self.api_orders_table.item(row, 0).text()
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, "Подтверждение удаления", 
                f"Вы уверены, что хотите удалить заказ #{order_id} из базы данных?\nЭто действие нельзя отменить.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Вызываем сигнал удаления API заказа
                self.delete_api_order_signal.emit(order_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления")

    def create_api_orders_tab(self):
        """Создание вкладки API заказов"""
        self.api_orders_tab = QWidget()
        self.api_orders_tab_layout = QVBoxLayout(self.api_orders_tab)
        
        # Добавляем информационное сообщение
        info_label = QLabel("Для получения актуальных данных о заказах из API нажмите кнопку 'Обновить заказы'. \n"
                          "Заказы, отсутствующие в новых данных, будут помечены как устаревшие и выделены серым цветом.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        self.api_orders_tab_layout.addWidget(info_label)
        
        # Создаем сплиттер для разделения списка заказов и деталей заказа
        splitter = QSplitter(Qt.Orientation.Vertical)
        orders_widget = QWidget()
        orders_layout = QVBoxLayout(orders_widget)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Верхняя часть: таблица заказов и кнопки управления
        self.api_orders_table = QTableWidget()
        self.api_orders_table.setColumnCount(10)
        self.api_orders_table.setHorizontalHeaderLabels([
            "ID заказа", "Статус", "Описание статуса", "Создан", "Количество", "Кол-во продуктов", 
            "Тип продукции", "Подписан", "Проверен", "Буферы"
        ])
        self.api_orders_table.itemSelectionChanged.connect(self.on_api_order_selected)
        orders_layout.addWidget(self.api_orders_table)
        
        # Кнопки управления заказами
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить заказы")
        refresh_button.clicked.connect(self.api_orders_signal.emit)
        buttons_layout.addWidget(refresh_button)
        
        create_order_button = QPushButton("Создать заказ на эмиссию")
        create_order_button.clicked.connect(self.on_create_emission_order_clicked)
        buttons_layout.addWidget(create_order_button)
        
        get_km_button = QPushButton("Получить КМ из заказа")
        get_km_button.clicked.connect(self.on_get_km_from_order_clicked)
        buttons_layout.addWidget(get_km_button)
        
        delete_button = QPushButton("Удалить заказ")
        delete_button.clicked.connect(self.on_delete_api_order_clicked)
        buttons_layout.addWidget(delete_button)
        
        orders_layout.addLayout(buttons_layout)
        
        # Нижняя часть: детали заказа (буферы)
        details_layout.addWidget(QLabel("Буферы кодов маркировки:"))
        self.api_buffers_table = QTableWidget()
        self.api_buffers_table.setColumnCount(9)
        self.api_buffers_table.setHorizontalHeaderLabels([
            "ID заказа", "GTIN", "Осталось в буфере", "Пулы исчерпаны", 
            "Всего кодов", "Недоступные коды", "Доступные коды", 
            "Всего передано", "OMS ID"
        ])
        details_layout.addWidget(self.api_buffers_table)
        
        # Добавляем виджеты в сплиттер
        splitter.addWidget(orders_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])
        
        # Добавляем сплиттер в макет вкладки
        self.api_orders_tab_layout.addWidget(splitter)
    
    def on_api_order_selected(self):
        """Обработчик выбора API заказа в таблице"""
        selected_rows = self.api_orders_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            # Получаем информацию о буферах из последней ячейки
            order_id = self.api_orders_table.item(row, 0).text()
            
            # Получаем API заказ из базы данных
            try:
                api_orders = self.db.get_api_orders()
                for api_order in api_orders:
                    if api_order.order_id == order_id:
                        # Обновляем таблицу буферов для выбранного заказа
                        self.update_api_buffers_table(api_order.buffers)
                        return
            except:
                # Если не удалось получить данные из базы, показываем пустую таблицу
                self.update_api_buffers_table([])
    
    def update_api_buffers_table(self, buffers):
        """Обновление таблицы буферов для выбранного API заказа
        
        Args:
            buffers (List[Dict]): Список буферов кодов маркировки
        """
        # Очищаем таблицу
        self.api_buffers_table.setRowCount(0)
        
        # Настраиваем столбцы - обновляем заголовки для соответствия с JSON
        self.api_buffers_table.setColumnCount(9)
        self.api_buffers_table.setHorizontalHeaderLabels([
            "ID заказа", "GTIN", "Осталось в буфере", "Пулы исчерпаны", 
            "Всего кодов", "Недоступные коды", "Доступные коды", 
            "Всего передано", "OMS ID"
        ])
        
        # Заполняем таблицу данными
        for i, buffer in enumerate(buffers):
            self.api_buffers_table.insertRow(i)
            
            # Заполняем ячейки таблицы согласно формату JSON
            self.api_buffers_table.setItem(i, 0, QTableWidgetItem(str(buffer.get("orderId", ""))))
            self.api_buffers_table.setItem(i, 1, QTableWidgetItem(str(buffer.get("gtin", ""))))
            self.api_buffers_table.setItem(i, 2, QTableWidgetItem(str(buffer.get("leftInBuffer", 0))))
            self.api_buffers_table.setItem(i, 3, QTableWidgetItem("Да" if buffer.get("poolsExhausted", False) else "Нет"))
            self.api_buffers_table.setItem(i, 4, QTableWidgetItem(str(buffer.get("totalCodes", 0))))
            self.api_buffers_table.setItem(i, 5, QTableWidgetItem(str(buffer.get("unavailableCodes", 0))))
            self.api_buffers_table.setItem(i, 6, QTableWidgetItem(str(buffer.get("availableCodes", 0))))
            self.api_buffers_table.setItem(i, 7, QTableWidgetItem(str(buffer.get("totalPassed", 0))))
            self.api_buffers_table.setItem(i, 8, QTableWidgetItem(str(buffer.get("omsId", ""))))
        
        # Подгоняем размеры колонок
        self.api_buffers_table.resizeColumnsToContents()
    
    def get_status_display_name(self, status_code):
        """Получение отображаемого имени статуса по коду"""
        status_map = {
            "CREATED": "Заказ создан",
            "PENDING": "Ожидает подтверждения",
            "DECLINED": "Не подтверждён",
            "APPROVED": "Подтверждён",
            "READY": "Готов",
            "CLOSED": "Закрыт",
            "UNKNOWN": "Неизвестный статус"
        }
        return status_map.get(status_code, status_code)
    
    def update_order_statuses_table(self, statuses):
        """Обновление таблицы статусов заказов"""
        self.order_statuses_table.setRowCount(len(statuses))
        for row, status in enumerate(statuses):
            self.order_statuses_table.setItem(row, 0, QTableWidgetItem(str(status.id)))
            self.order_statuses_table.setItem(row, 1, QTableWidgetItem(status.code))
            self.order_statuses_table.setItem(row, 2, QTableWidgetItem(status.name))
            self.order_statuses_table.setItem(row, 3, QTableWidgetItem(status.description))

    def on_get_km_from_order_clicked(self):
        """Обработчик нажатия кнопки получения КМ из заказа"""
        # Получаем выбранный заказ
        selected_rows = self.api_orders_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для получения КМ")
            return
            
        row = selected_rows[0].row()
        order_id = self.api_orders_table.item(row, 0).text()
        
        # Проверяем статус заказа - должен быть READY
        status = self.api_orders_table.item(row, 1).text()
        if status != "READY":
            QMessageBox.warning(self, "Ошибка", 
                f"Невозможно получить КМ из заказа со статусом '{status}'. Статус заказа должен быть 'READY'.")
            return
        
        # Получаем буферы для выбранного заказа
        gtins = []
        try:
            api_orders = self.db.get_api_orders()
            for api_order in api_orders:
                if api_order.order_id == order_id:
                    # Собираем GTINы из буферов
                    for buffer in api_order.buffers:
                        gtin = buffer.get("gtin")
                        if gtin and gtin not in gtins:
                            gtins.append(gtin)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении информации о буферах: {str(e)}")
            return
        
        # Если GTINы не найдены, выводим сообщение
        if not gtins:
            QMessageBox.warning(self, "Ошибка", "Не найдены GTINы для выбранного заказа")
            return
            
        # Создаем диалог для выбора GTIN и количества КМ
        from views.dialogs import GetKMDialog
        dialog = GetKMDialog(self, order_id, gtins)
        
        # Если пользователь нажал "OK", отправляем сигнал на получение КМ
        if dialog.exec():
            data = dialog.get_data()
            gtin = data.get("gtin")
            quantity = data.get("quantity")
            
            # Отправляем сигнал на получение КМ
            self.get_km_from_order_signal.emit(order_id, gtin, quantity)
    
    def display_codes_from_order(self, order_id, gtin, codes):
        """Отображение полученных КМ из заказа
        
        Args:
            order_id (str): Идентификатор заказа
            gtin (str): GTIN товара
            codes (List[str]): Список кодов маркировки
        """
        from views.dialogs import DisplayCodesDialog
        dialog = DisplayCodesDialog(self, order_id, gtin, codes)
        dialog.exec()

    def create_marking_codes_tab(self):
        """Создание вкладки для просмотра кодов маркировки"""
        self.marking_codes_tab = QWidget()
        layout = QVBoxLayout(self.marking_codes_tab)
        
        # Добавляем фильтры
        filters_layout = QHBoxLayout()
        
        # Фильтр по GTIN
        gtin_layout = QHBoxLayout()
        gtin_label = QLabel("GTIN:")
        self.gtin_filter = QLineEdit()
        self.gtin_filter.setPlaceholderText("Введите GTIN для фильтрации")
        gtin_layout.addWidget(gtin_label)
        gtin_layout.addWidget(self.gtin_filter)
        filters_layout.addLayout(gtin_layout)
        
        # Фильтр по ID заказа
        order_id_layout = QHBoxLayout()
        order_id_label = QLabel("ID заказа:")
        self.order_id_filter = QLineEdit()
        self.order_id_filter.setPlaceholderText("Введите ID заказа для фильтрации")
        order_id_layout.addWidget(order_id_label)
        order_id_layout.addWidget(self.order_id_filter)
        filters_layout.addLayout(order_id_layout)
        
        # Чекбоксы для фильтрации
        self.used_filter = QCheckBox("Только неиспользованные")
        self.used_filter.setChecked(True)
        filters_layout.addWidget(self.used_filter)
        
        self.exported_filter = QCheckBox("Только неэкспортированные")
        self.exported_filter.setChecked(True)
        filters_layout.addWidget(self.exported_filter)
        
        # Кнопка применения фильтров
        apply_filter_button = QPushButton("Применить фильтры")
        apply_filter_button.clicked.connect(self.on_apply_marking_codes_filter)
        filters_layout.addWidget(apply_filter_button)
        
        layout.addLayout(filters_layout)
        
        # Таблица кодов маркировки
        self.marking_codes_table = QTableWidget()
        self.marking_codes_table.setColumnCount(7)
        self.marking_codes_table.setHorizontalHeaderLabels([
            "ID", "Код маркировки", "GTIN", "ID заказа", "Использован", "Экспортирован", "Создан"
        ])
        layout.addWidget(self.marking_codes_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.on_refresh_marking_codes)
        buttons_layout.addWidget(refresh_button)
        
        export_button = QPushButton("Экспортировать выбранные")
        export_button.clicked.connect(self.on_export_marking_codes)
        buttons_layout.addWidget(export_button)
        
        mark_used_button = QPushButton("Отметить как использованные")
        mark_used_button.clicked.connect(self.on_mark_codes_as_used)
        buttons_layout.addWidget(mark_used_button)
        
        layout.addLayout(buttons_layout)
        
    def on_apply_marking_codes_filter(self):
        """Обработчик нажатия кнопки применения фильтров кодов маркировки"""
        # Получаем значения фильтров
        gtin = self.gtin_filter.text().strip() if self.gtin_filter.text().strip() else None
        order_id = self.order_id_filter.text().strip() if self.order_id_filter.text().strip() else None
        used = not self.used_filter.isChecked()  # Инвертируем, т.к. чекбокс "Только неиспользованные"
        exported = not self.exported_filter.isChecked()  # Инвертируем, т.к. чекбокс "Только неэкспортированные"
        
        # Отправляем сигнал на получение кодов с фильтрами
        self.get_marking_codes_signal.emit({"gtin": gtin, "order_id": order_id, "used": used, "exported": exported})
    
    def on_refresh_marking_codes(self):
        """Обработчик нажатия кнопки обновления кодов маркировки"""
        # Получаем текущие значения фильтров и отправляем сигнал
        self.on_apply_marking_codes_filter()
    
    def on_export_marking_codes(self):
        """Обработчик нажатия кнопки экспорта выбранных кодов маркировки"""
        # Получаем выбранные строки
        selected_rows = self.marking_codes_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Не выбраны коды для экспорта")
            return
        
        # Создаем список выбранных ID и кодов маркировки
        code_ids = []
        codes = []
        rows = set()
        
        for item in selected_rows:
            row = item.row()
            if row not in rows:
                rows.add(row)
                code_id = int(self.marking_codes_table.item(row, 0).text())
                code = self.marking_codes_table.item(row, 1).text()
                code_ids.append(code_id)
                codes.append(code)
        
        # Если выбраны коды, открываем диалог сохранения
        if codes:
            from views.dialogs import DisplayCodesDialog
            
            # Используем первый выбранный код для определения GTIN и order_id
            gtin = self.marking_codes_table.item(list(rows)[0], 2).text()
            order_id = self.marking_codes_table.item(list(rows)[0], 3).text()
            
            # Открываем диалог отображения кодов
            dialog = DisplayCodesDialog(self, order_id, gtin, codes)
            result = dialog.exec()
            
            # Если диалог был принят, отправляем сигнал для отметки кодов как экспортированных
            if result:
                self.mark_codes_as_exported_signal.emit(code_ids)
    
    def on_mark_codes_as_used(self):
        """Обработчик нажатия кнопки отметки кодов как использованных"""
        # Получаем выбранные строки
        selected_rows = self.marking_codes_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Не выбраны коды для отметки")
            return
        
        # Создаем список выбранных ID
        code_ids = []
        rows = set()
        
        for item in selected_rows:
            row = item.row()
            if row not in rows:
                rows.add(row)
                code_id = int(self.marking_codes_table.item(row, 0).text())
                code_ids.append(code_id)
        
        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self, "Подтверждение", 
            f"Вы уверены, что хотите отметить {len(code_ids)} кодов как использованные?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Отправляем сигнал для отметки кодов как использованных
            self.mark_codes_as_used_signal.emit(code_ids)
    
    def update_marking_codes_table(self, codes):
        """Обновление таблицы кодов маркировки
        
        Args:
            codes (List[Dict]): Список словарей с данными кодов маркировки
        """
        # Очищаем таблицу
        self.marking_codes_table.setRowCount(0)
        
        # Заполняем таблицу данными
        for i, code_data in enumerate(codes):
            self.marking_codes_table.insertRow(i)
            
            # ID
            self.marking_codes_table.setItem(i, 0, QTableWidgetItem(str(code_data["id"])))
            
            # Код маркировки
            code_item = QTableWidgetItem(code_data["code"])
            # Если код использован, делаем его серым
            if code_data["used"]:
                code_item.setForeground(QColor(150, 150, 150))
            self.marking_codes_table.setItem(i, 1, code_item)
            
            # GTIN
            self.marking_codes_table.setItem(i, 2, QTableWidgetItem(code_data["gtin"]))
            
            # ID заказа
            self.marking_codes_table.setItem(i, 3, QTableWidgetItem(code_data["order_id"]))
            
            # Использован
            used_item = QTableWidgetItem("Да" if code_data["used"] else "Нет")
            if code_data["used"]:
                used_item.setForeground(QColor(150, 150, 150))
            self.marking_codes_table.setItem(i, 4, used_item)
            
            # Экспортирован
            exported_item = QTableWidgetItem("Да" if code_data["exported"] else "Нет")
            if code_data["exported"]:
                exported_item.setForeground(QColor(150, 150, 150))
            self.marking_codes_table.setItem(i, 5, exported_item)
            
            # Создан
            self.marking_codes_table.setItem(i, 6, QTableWidgetItem(code_data["created_at"]))
        
        # Подгоняем размеры колонок
        self.marking_codes_table.resizeColumnsToContents()
        
        # Обновляем счетчик
        if codes:
            self.tabs.setTabText(self.tabs.indexOf(self.marking_codes_tab), f"Коды маркировки ({len(codes)})")
        else:
            self.tabs.setTabText(self.tabs.indexOf(self.marking_codes_tab), "Коды маркировки")

    def create_aggregation_files_tab(self):
        """Создание вкладки для работы с файлами агрегации"""
        self.aggregation_files_tab = QWidget()
        layout = QVBoxLayout(self.aggregation_files_tab)
        
        # Создаем таблицу для отображения файлов агрегации
        self.aggregation_files_table = QTableWidget()
        self.aggregation_files_table.setColumnCount(6)
        self.aggregation_files_table.setHorizontalHeaderLabels([
            "Имя файла", "Продукция", "Коды маркировки", "Коды агрегации 1 уровня", 
            "Коды агрегации 2 уровня", "Комментарий"
        ])
        self.aggregation_files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.aggregation_files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.aggregation_files_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.aggregation_files_table.customContextMenuRequested.connect(self.show_aggregation_file_context_menu)
        
        layout.addWidget(self.aggregation_files_table)
        
        # Создаем панель с кнопками
        button_layout = QHBoxLayout()
        
        # Кнопка для загрузки файла
        load_file_button = QPushButton("Загрузить файл")
        load_file_button.clicked.connect(self.on_load_aggregation_file)
        button_layout.addWidget(load_file_button)
        
        # Кнопка для отправки отчета о нанесении
        send_utilisation_report_button = QPushButton("Отчет о нанесении")
        send_utilisation_report_button.clicked.connect(self.on_send_utilisation_report)
        button_layout.addWidget(send_utilisation_report_button)
        
        # Кнопка для обновления списка файлов
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_aggregation_files_signal.emit)
        button_layout.addWidget(refresh_button)
        
        layout.addLayout(button_layout)

    def on_send_utilisation_report(self):
        """Обработчик нажатия на кнопку 'Отчет о нанесении'"""
        # Проверяем, что выбрана строка в таблице файлов агрегации
        if not self.aggregation_files_table.selectedItems():
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Необходимо выбрать файл агрегации для формирования отчета о нанесении."
            )
            return
        
        # Получаем ID выбранного файла
        row = self.aggregation_files_table.selectedItems()[0].row()
        file_id = int(self.aggregation_files_table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        
        # Создаем диалог для предварительного просмотра и редактирования отчета
        # Передаем контроллер явно в качестве дополнительного параметра
        dialog = UtilisationReportDialog(file_id, self, self.controller)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Получаем данные отчета из диалога
            report_data = dialog.get_report_data()
            
            # Отправляем сигнал на отправку отчета
            self.send_utilisation_report_signal.emit(report_data)

    def show_aggregation_file_context_menu(self, position):
        """Отображение контекстного меню для таблицы файлов агрегации"""
        menu = QMenu()
        export_action = menu.addAction("Выгрузить JSON")
        utilisation_action = menu.addAction("Отчет о нанесении")
        delete_action = menu.addAction("Удалить")
        
        # Проверяем, что выбрана строка
        if not self.aggregation_files_table.selectedItems():
            export_action.setEnabled(False)
            utilisation_action.setEnabled(False)
            delete_action.setEnabled(False)
        
        action = menu.exec(self.aggregation_files_table.mapToGlobal(position))
        
        if not self.aggregation_files_table.selectedItems():
            return
        
        # Получаем ID выбранного файла (хранится в теге)
        row = self.aggregation_files_table.selectedItems()[0].row()
        file_id = int(self.aggregation_files_table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        
        if action == export_action:
            # Открываем диалог выбора пути для сохранения файла
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Выгрузить JSON-файл",
                f"{self.aggregation_files_table.item(row, 0).text()}.json",
                "JSON файлы (*.json)"
            )
            
            if file_path:
                # Отправляем сигнал на выгрузку файла
                self.export_aggregation_file_signal.emit(file_id, file_path)
        
        elif action == utilisation_action:
            # Открываем диалог для создания отчета о нанесении
            self.on_send_utilisation_report()
        
        elif action == delete_action:
            # Запрашиваем подтверждение
            if QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы действительно хотите удалить файл агрегации?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                # Отправляем сигнал на удаление файла
                self.delete_aggregation_file_signal.emit(file_id)

    def on_load_aggregation_file(self):
        """Обработчик нажатия на кнопку 'Загрузить файл'"""
        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл агрегации",
            "",
            "JSON файлы (*.json)"
        )
        
        if file_path:
            # Запрашиваем комментарий
            comment, ok = QInputDialog.getText(
                self,
                "Комментарий",
                "Введите комментарий к файлу:"
            )
            
            if ok:  # Пользователь нажал OK
                try:
                    # Получаем имя файла из пути
                    filename = os.path.basename(file_path)
                    
                    # Читаем данные из JSON-файла
                    with open(file_path, 'r', encoding='utf-8') as file:
                        json_text = file.read()
                    data = json.loads(json_text)
                    
                    # Логирование для отладки
                    logging.info(f"Загружен файл: {filename}")
                    logging.info(f"Содержимое файла: {json_text[:100]}...")  # Логируем первые 100 символов
                    
                    # Отправляем сигнал на добавление файла
                    self.add_aggregation_file_signal.emit(filename, data, comment)
                    
                except json.JSONDecodeError as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при разборе JSON-файла: {str(e)}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при чтении файла: {str(e)}"
                    )

    def update_aggregation_files_table(self, files):
        """Обновление таблицы файлов агрегации
        
        Args:
            files (List[AggregationFile]): Список объектов файлов агрегации
        """
        # Логирование для отладки
        logging.info(f"Обновление таблицы файлов агрегации. Получено {len(files)} файлов.")
        
        self.aggregation_files_table.setRowCount(0)  # Очищаем таблицу
        
        for file in files:
            # Логирование информации о файле
            logging.info(f"Добавление файла в таблицу: {file.filename}")
            logging.info(f"Продукция: {file.product}")
            logging.info(f"Кол-во кодов маркировки: {len(file.marking_codes)}")
            logging.info(f"Кол-во кодов агрегации 1 уровня: {len(file.level1_codes)}")
            logging.info(f"Кол-во кодов агрегации 2 уровня: {len(file.level2_codes)}")
            
            row = self.aggregation_files_table.rowCount()
            self.aggregation_files_table.insertRow(row)
            
            # Имя файла
            item = QTableWidgetItem(file.filename)
            item.setData(Qt.ItemDataRole.UserRole, file.id)  # Сохраняем ID в теге
            self.aggregation_files_table.setItem(row, 0, item)
            
            # Продукция
            item = QTableWidgetItem(file.product)
            self.aggregation_files_table.setItem(row, 1, item)
            
            # Коды маркировки
            item = QTableWidgetItem(str(len(file.marking_codes)))
            self.aggregation_files_table.setItem(row, 2, item)
            
            # Коды агрегации 1 уровня
            item = QTableWidgetItem(str(len(file.level1_codes)))
            self.aggregation_files_table.setItem(row, 3, item)
            
            # Коды агрегации 2 уровня
            item = QTableWidgetItem(str(len(file.level2_codes)))
            self.aggregation_files_table.setItem(row, 4, item)
            
            # Комментарий
            item = QTableWidgetItem(file.comment)
            self.aggregation_files_table.setItem(row, 5, item)
        
        # Подгоняем ширину колонок
        self.aggregation_files_table.resizeColumnsToContents()

class CatalogsDialog(QDialog):
    """Диалог для работы со справочниками"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочники")
        self.resize(800, 600)
        
        # Получаем ссылку на главное окно
        self.main_window = parent
        
        # Подключаем сигналы главного окна к слотам обновления таблиц
        self.main_window.add_nomenclature_signal.connect(self.reload_nomenclature)
        self.main_window.edit_nomenclature_signal.connect(self.reload_nomenclature)
        self.main_window.delete_nomenclature_signal.connect(self.reload_nomenclature)
        self.main_window.set_active_extension_signal.connect(self.reload_extensions)
        self.main_window.load_countries_signal.connect(self.reload_countries)
        self.main_window.load_order_statuses_signal.connect(self.reload_order_statuses)
        self.main_window.add_order_status_signal.connect(self.reload_order_statuses)
        self.main_window.edit_order_status_signal.connect(self.reload_order_statuses)
        self.main_window.delete_order_status_signal.connect(self.reload_order_statuses)
        
        layout = QVBoxLayout(self)
        
        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Создаем вкладки
        self.create_nomenclature_tab()
        self.create_extensions_tab()
        self.create_countries_tab()
        self.create_order_statuses_tab()
        self.create_usage_types_tab()  # Новая вкладка для типов использования
        
        # Добавляем вкладки в виджет
        self.tabs.addTab(self.nomenclature_tab, "Номенклатура")
        self.tabs.addTab(self.extensions_tab, "Виды продукции")
        self.tabs.addTab(self.countries_tab, "Страны")
        self.tabs.addTab(self.order_statuses_tab, "Статусы заказов")
        self.tabs.addTab(self.usage_types_tab, "Типы использования")  # Добавляем новую вкладку
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Подключаем обработчик изменения активной вкладки
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def showEvent(self, event):
        """Обработчик события показа диалога"""
        # Обновляем данные всех таблиц при показе диалога
        self.reload_nomenclature()
        self.reload_extensions()
        self.reload_countries()
        self.reload_order_statuses()
        self.reload_usage_types()  # Загружаем типы использования
        super().showEvent(event)
    
    def on_tab_changed(self, index):
        """Обработчик изменения активной вкладки"""
        # Обновляем данные таблицы при переключении на нее
        if index == 0:  # Номенклатура
            self.reload_nomenclature()
        elif index == 1:  # Расширения
            self.reload_extensions()
        elif index == 2:  # Страны
            self.reload_countries()
        elif index == 3:  # Статусы заказов
            self.reload_order_statuses()
        elif index == 4:  # Типы использования
            self.reload_usage_types()

    def create_nomenclature_tab(self):
        """Создание вкладки номенклатуры"""
        self.nomenclature_tab = QWidget()
        layout = QVBoxLayout(self.nomenclature_tab)
        
        # Создаем копию таблицы номенклатуры и подключаем данные
        self.nomenclature_table = QTableWidget()
        self.nomenclature_table.setColumnCount(4)
        self.nomenclature_table.setHorizontalHeaderLabels(["ID", "Название", "GTIN", "Описание"])
        layout.addWidget(self.nomenclature_table)
        
        # Создаем кнопки для управления номенклатурой
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_nomenclature_clicked)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_nomenclature_clicked)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_nomenclature_clicked)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
    
    def create_extensions_tab(self):
        """Создание вкладки расширений API"""
        self.extensions_tab = QWidget()
        layout = QVBoxLayout(self.extensions_tab)
        
        # Таблица расширений API
        self.extensions_table = QTableWidget()
        self.extensions_table.setColumnCount(4)
        self.extensions_table.setHorizontalHeaderLabels(["ID", "Название", "Код", "Активный"])
        layout.addWidget(self.extensions_table)
        
        # Кнопки управления расширениями API
        buttons_layout = QHBoxLayout()
        
        set_active_button = QPushButton("Установить активным")
        set_active_button.clicked.connect(self.on_set_active_extension)
        buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(buttons_layout)
    
    def on_set_active_extension(self):
        """Обработчик нажатия кнопки установки активного расширения"""
        row = self.extensions_table.currentRow()
        if row >= 0:
            extension_id = int(self.extensions_table.item(row, 0).text())
            self.main_window.set_active_extension_signal.emit(extension_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите вид продукции для активации")
    
    def reload_extensions(self, *args):
        """Обновить таблицу расширений в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.extensions_table
        self.extensions_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.extensions_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.extensions_table.resizeColumnsToContents()
    
    def create_countries_tab(self):
        """Создание вкладки стран"""
        self.countries_tab = QWidget()
        layout = QVBoxLayout(self.countries_tab)
        
        # Таблица стран
        self.countries_table = QTableWidget()
        self.countries_table.setColumnCount(3)
        self.countries_table.setHorizontalHeaderLabels(["ID", "Код", "Название"])
        layout.addWidget(self.countries_table)
        
        # В этой вкладке обычно нет кнопок управления, так как
        # список стран обычно загружается из API и не редактируется пользователем
    
    def create_order_statuses_tab(self):
        """Создание вкладки статусов заказов"""
        self.order_statuses_tab = QWidget()
        layout = QVBoxLayout(self.order_statuses_tab)
        
        # Таблица статусов заказов
        self.order_statuses_table = QTableWidget()
        self.order_statuses_table.setColumnCount(4)
        self.order_statuses_table.setHorizontalHeaderLabels(["ID", "Код", "Название", "Описание"])
        layout.addWidget(self.order_statuses_table)
        
        # Кнопки управления статусами
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(lambda: self.main_window.load_order_statuses_signal.emit())
        buttons_layout.addWidget(refresh_button)
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_order_status_clicked)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_order_status_clicked)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_order_status_clicked)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
        
    def reload_countries(self, *args):
        """Обновить таблицу стран в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.countries_table
        self.countries_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.countries_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.countries_table.resizeColumnsToContents()
    
    def reload_nomenclature(self, *args):
        """Обновить таблицу номенклатуры в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.nomenclature_table
        self.nomenclature_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.nomenclature_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.nomenclature_table.resizeColumnsToContents()
    
    def reload_order_statuses(self, *args):
        """Обновить таблицу статусов заказов в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.order_statuses_table
        self.order_statuses_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.order_statuses_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.order_statuses_table.resizeColumnsToContents()

    def on_add_nomenclature_clicked(self):
        """Обработчик нажатия кнопки добавления номенклатуры в диалоге Справочники"""
        # Получаем список расширений API
        extensions = []
        source_table = self.main_window.extensions_table
        for row in range(source_table.rowCount()):
            extension_id = int(source_table.item(row, 0).text())
            extension_name = source_table.item(row, 1).text()
            extension_code = source_table.item(row, 2).text()
            is_active = source_table.item(row, 3).text() == "Да"
            extensions.append(Extension(extension_id, extension_code, extension_name, is_active))
        
        dialog = NomenclatureDialog(self, extensions=extensions)
        if dialog.exec():
            data = dialog.get_data()
            self.main_window.add_nomenclature_signal.emit(data['name'], data['gtin'], data['product_group'])
    
    def on_edit_nomenclature_clicked(self):
        """Обработчик нажатия кнопки редактирования номенклатуры в диалоге Справочники"""
        row = self.nomenclature_table.currentRow()
        if row >= 0:
            nomenclature_id = int(self.nomenclature_table.item(row, 0).text())
            name = self.nomenclature_table.item(row, 1).text()
            gtin = self.nomenclature_table.item(row, 2).text()
            product_group = self.nomenclature_table.item(row, 3).text() if self.nomenclature_table.item(row, 3) else ""
            
            # Создаем объект номенклатуры
            nomenclature = Nomenclature(nomenclature_id, name, gtin, product_group)
            
            # Получаем список расширений API перед открытием диалога
            extensions = []
            source_table = self.main_window.extensions_table
            for row in range(source_table.rowCount()):
                extension_id = int(source_table.item(row, 0).text())
                extension_name = source_table.item(row, 1).text()
                extension_code = source_table.item(row, 2).text()
                is_active = source_table.item(row, 3).text() == "Да"
                extensions.append(Extension(extension_id, extension_code, extension_name, is_active))
            
            # Открываем диалог редактирования
            dialog = NomenclatureDialog(self, nomenclature=nomenclature, extensions=extensions)
            if dialog.exec():
                data = dialog.get_data()
                self.main_window.edit_nomenclature_signal.emit(nomenclature_id, data['name'], data['gtin'], data['product_group'])
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите номенклатуру для редактирования")
    
    def on_delete_nomenclature_clicked(self):
        """Обработчик нажатия кнопки удаления номенклатуры в диалоге Справочники"""
        row = self.nomenclature_table.currentRow()
        if row >= 0:
            nomenclature_id = int(self.nomenclature_table.item(row, 0).text())
            self.main_window.delete_nomenclature_signal.emit(nomenclature_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите номенклатуру для удаления")
    
    def on_add_order_status_clicked(self):
        """Обработчик нажатия кнопки добавления статуса заказа"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        # Запрашиваем код статуса
        code, ok = QInputDialog.getText(
            self, "Добавление статуса заказа", "Введите код статуса:", QLineEdit.EchoMode.Normal
        )
        
        if ok and code:
            # Запрашиваем название статуса
            name, ok = QInputDialog.getText(
                self, "Добавление статуса заказа", "Введите название статуса:", QLineEdit.EchoMode.Normal
            )
            
            if ok and name:
                # Запрашиваем описание статуса
                description, ok = QInputDialog.getText(
                    self, "Добавление статуса заказа", "Введите описание статуса:", QLineEdit.EchoMode.Normal
                )
                
                if ok:
                    # Вызываем сигнал добавления статуса
                    self.main_window.add_order_status_signal.emit(code, name, description)
    
    def on_edit_order_status_clicked(self):
        """Обработчик нажатия кнопки редактирования статуса заказа"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        row = self.order_statuses_table.currentRow()
        if row >= 0:
            status_id = int(self.order_statuses_table.item(row, 0).text())
            code = self.order_statuses_table.item(row, 1).text()
            name = self.order_statuses_table.item(row, 2).text()
            description = self.order_statuses_table.item(row, 3).text() if self.order_statuses_table.item(row, 3) else ""
            
            # Запрашиваем новый код статуса
            new_code, ok = QInputDialog.getText(
                self, "Редактирование статуса заказа", "Введите код статуса:", QLineEdit.EchoMode.Normal, code
            )
            
            if ok and new_code:
                # Запрашиваем новое название статуса
                new_name, ok = QInputDialog.getText(
                    self, "Редактирование статуса заказа", "Введите название статуса:", QLineEdit.EchoMode.Normal, name
                )
                
                if ok and new_name:
                    # Запрашиваем новое описание статуса
                    new_description, ok = QInputDialog.getText(
                        self, "Редактирование статуса заказа", "Введите описание статуса:", QLineEdit.EchoMode.Normal, description
                    )
                    
                    if ok:
                        # Вызываем сигнал редактирования статуса из главного окна
                        self.main_window.edit_order_status_signal.emit(status_id, new_code, new_name, new_description)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите статус заказа для редактирования")
    
    def on_delete_order_status_clicked(self):
        """Обработчик нажатия кнопки удаления статуса заказа"""
        row = self.order_statuses_table.currentRow()
        if row >= 0:
            status_id = int(self.order_statuses_table.item(row, 0).text())
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, "Подтверждение удаления", 
                "Вы уверены, что хотите удалить этот статус заказа?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Вызываем сигнал удаления статуса из главного окна
                self.main_window.delete_order_status_signal.emit(status_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите статус заказа для удаления")

    def create_usage_types_tab(self):
        """Создание вкладки типов использования кодов маркировки"""
        self.usage_types_tab = QWidget()
        layout = QVBoxLayout(self.usage_types_tab)
        
        # Таблица типов использования
        self.usage_types_table = QTableWidget()
        self.usage_types_table.setColumnCount(4)
        self.usage_types_table.setHorizontalHeaderLabels(["ID", "Код", "Название", "Описание"])
        layout.addWidget(self.usage_types_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.reload_usage_types)
        buttons_layout.addWidget(refresh_button)
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_usage_type_clicked)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_usage_type_clicked)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_usage_type_clicked)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
    
    def reload_usage_types(self, *args):
        """Обновить таблицу типов использования кодов маркировки"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Загрузка типов использования кодов маркировки")
            
            # Получаем данные из базы через контроллер главного окна
            if not hasattr(self.main_window, 'controller') or not self.main_window.controller:
                logger.error("Отсутствует контроллер")
                return
            
            # Получаем типы использования через метод контроллера
            usage_types = self.main_window.controller.load_usage_types()
            
            # Очищаем таблицу
            self.usage_types_table.setRowCount(0)
            
            # Заполняем таблицу данными
            for i, usage_type in enumerate(usage_types):
                self.usage_types_table.insertRow(i)
                
                # ID
                id_item = QTableWidgetItem(str(usage_type.id))
                self.usage_types_table.setItem(i, 0, id_item)
                
                # Код
                code_item = QTableWidgetItem(usage_type.code)
                self.usage_types_table.setItem(i, 1, code_item)
                
                # Название
                name_item = QTableWidgetItem(usage_type.name)
                self.usage_types_table.setItem(i, 2, name_item)
                
                # Описание
                description_item = QTableWidgetItem(usage_type.description or "")
                self.usage_types_table.setItem(i, 3, description_item)
            
            # Подгоняем ширину колонок
            self.usage_types_table.resizeColumnsToContents()
            
            logger.info(f"Загружено {len(usage_types)} типов использования")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке типов использования: {str(e)}")
            logger.exception("Подробная трассировка ошибки:")
    
    def on_add_usage_type_clicked(self):
        """Обработчик нажатия кнопки добавления типа использования"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Попытка добавления типа использования")
        
        try:
            # Запрашиваем код типа использования
            code, ok = QInputDialog.getText(
                self, "Добавление типа использования", "Введите код типа использования:", QLineEdit.EchoMode.Normal
            )
            
            if ok and code:
                # Запрашиваем название типа использования
                name, ok = QInputDialog.getText(
                    self, "Добавление типа использования", "Введите название типа использования:", QLineEdit.EchoMode.Normal
                )
                
                if ok and name:
                    # Запрашиваем описание типа использования
                    description, ok = QInputDialog.getText(
                        self, "Добавление типа использования", "Введите описание типа использования:", QLineEdit.EchoMode.Normal
                    )
                    
                    if ok:
                        # Проверка ввода
                        if not code.strip():
                            logger.error("Код типа использования не может быть пустым")
                            QMessageBox.critical(self, "Ошибка", "Код типа использования не может быть пустым")
                            return
                        
                        if not name.strip():
                            logger.error("Название типа использования не может быть пустым")
                            QMessageBox.critical(self, "Ошибка", "Название типа использования не может быть пустым")
                            return
                        
                        # Добавляем тип использования через сигнал главного окна
                        logger.info(f"Отправка сигнала add_usage_type_signal: код={code}, название={name}")
                        self.main_window.add_usage_type_signal.emit(code, name, description or "")
                        
                        # Обновляем таблицу через некоторое время, чтобы дать время контроллеру обработать запрос
                        QTimer.singleShot(500, self.reload_usage_types)
        except Exception as e:
            logger.exception(f"Исключение при добавлении типа использования: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить тип использования: {str(e)}")
    
    def on_edit_usage_type_clicked(self):
        """Обработчик нажатия кнопки редактирования типа использования"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        row = self.usage_types_table.currentRow()
        if row >= 0:
            usage_type_id = int(self.usage_types_table.item(row, 0).text())
            code = self.usage_types_table.item(row, 1).text()
            name = self.usage_types_table.item(row, 2).text()
            description = self.usage_types_table.item(row, 3).text() if self.usage_types_table.item(row, 3) else ""
            
            # Запрашиваем новый код типа использования
            new_code, ok = QInputDialog.getText(
                self, "Редактирование типа использования", "Введите код типа использования:", QLineEdit.EchoMode.Normal, code
            )
            
            if ok and new_code:
                # Запрашиваем новое название типа использования
                new_name, ok = QInputDialog.getText(
                    self, "Редактирование типа использования", "Введите название типа использования:", QLineEdit.EchoMode.Normal, name
                )
                
                if ok and new_name:
                    # Запрашиваем новое описание типа использования
                    new_description, ok = QInputDialog.getText(
                        self, "Редактирование типа использования", "Введите описание типа использования:", QLineEdit.EchoMode.Normal, description
                    )
                    
                    if ok:
                        try:
                            # Обновляем тип использования через контроллер
                            if self.main_window.controller:
                                self.main_window.controller.update_usage_type(usage_type_id, new_code, new_name, new_description)
                                # Обновляем таблицу
                                self.reload_usage_types()
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить тип использования: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите тип использования для редактирования")
    
    def on_delete_usage_type_clicked(self):
        """Обработчик нажатия кнопки удаления типа использования"""
        row = self.usage_types_table.currentRow()
        if row >= 0:
            usage_type_id = int(self.usage_types_table.item(row, 0).text())
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, "Подтверждение удаления", 
                "Вы уверены, что хотите удалить этот тип использования?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # Удаляем тип использования через контроллер
                    if self.main_window.controller:
                        self.main_window.controller.delete_usage_type(usage_type_id)
                        # Обновляем таблицу
                        self.reload_usage_types()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тип использования: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите тип использования для удаления")

class SettingsDialog(QDialog):
    """Диалог для работы с настройками"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(800, 600)
        
        # Получаем ссылку на главное окно
        self.main_window = parent
        
        # Подключаем сигналы главного окна к слотам обновления таблиц
        self.main_window.add_connection_signal.connect(self.reload_connections)
        self.main_window.edit_connection_signal.connect(self.reload_connections)
        self.main_window.delete_connection_signal.connect(self.reload_connections)
        self.main_window.set_active_connection_signal.connect(self.reload_connections)
        self.main_window.add_credentials_signal.connect(self.reload_credentials)
        self.main_window.edit_credentials_signal.connect(self.reload_credentials)
        self.main_window.delete_credentials_signal.connect(self.reload_credentials)
        
        layout = QVBoxLayout(self)
        
        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Создаем вкладки
        self.create_connections_tab()
        self.create_credentials_tab()
        self.create_general_settings_tab()
        
        # Добавляем вкладки в виджет
        self.tabs.addTab(self.connections_tab, "Подключения")
        self.tabs.addTab(self.credentials_tab, "Учетные данные")
        self.tabs.addTab(self.general_settings_tab, "Общие настройки")
        
        # Кнопки Ok/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Подключаем обработчик изменения активной вкладки
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def showEvent(self, event):
        """Обработчик события показа диалога"""
        # Обновляем данные всех таблиц при показе диалога
        self.reload_connections()
        self.reload_credentials()
        super().showEvent(event)
    
    def on_tab_changed(self, index):
        """Обработчик изменения активной вкладки"""
        # Обновляем данные таблицы при переключении на нее
        if index == 0:  # Подключения
            self.reload_connections()
        elif index == 1:  # Учетные данные
            self.reload_credentials()

    def create_connections_tab(self):
        """Создание вкладки подключений"""
        self.connections_tab = QWidget()
        layout = QVBoxLayout(self.connections_tab)
        
        # Создаем копию таблицы подключений и подключаем данные
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(4)
        self.connections_table.setHorizontalHeaderLabels(["ID", "Название", "URL", "Активный"])
        
        # Первоначальное заполнение таблицы
        self.reload_connections()
        
        layout.addWidget(self.connections_table)
        
        # Кнопки управления подключениями
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_connection)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_connection)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_connection)
        buttons_layout.addWidget(delete_button)
        
        set_active_button = QPushButton("Установить активным")
        set_active_button.clicked.connect(self.on_set_active_connection)
        buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(buttons_layout)
    
    def reload_connections(self, *args):
        """Обновить таблицу подключений в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.connections_table
        self.connections_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.connections_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.connections_table.resizeColumnsToContents()
    
    def on_add_connection(self):
        """Обработчик нажатия кнопки добавления подключения в диалоге"""
        from views.dialogs import ConnectionDialog
        dialog = ConnectionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.main_window.add_connection_signal.emit(data['name'], data['url'])
    
    def on_edit_connection(self):
        """Обработчик нажатия кнопки редактирования подключения в диалоге"""
        from views.dialogs import ConnectionDialog
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            name = self.connections_table.item(row, 1).text()
            url = self.connections_table.item(row, 2).text()
            
            dialog = ConnectionDialog(self)
            # Заполняем поля текущими значениями
            dialog.name_input.setText(name)
            dialog.url_input.setText(url)
            
            if dialog.exec():
                data = dialog.get_data()
                self.main_window.edit_connection_signal.emit(connection_id, data['name'], data['url'])
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для редактирования")
    
    def on_delete_connection(self):
        """Обработчик нажатия кнопки удаления подключения в диалоге"""
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            self.main_window.delete_connection_signal.emit(connection_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для удаления")
    
    def on_set_active_connection(self):
        """Обработчик нажатия кнопки установки активного подключения в диалоге"""
        row = self.connections_table.currentRow()
        if row >= 0:
            connection_id = int(self.connections_table.item(row, 0).text())
            self.main_window.set_active_connection_signal.emit(connection_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение для активации")
    
    def create_credentials_tab(self):
        """Создание вкладки учетных данных"""
        self.credentials_tab = QWidget()
        layout = QVBoxLayout(self.credentials_tab)
        
        # Создаем копию таблицы учетных данных и подключаем данные
        self.credentials_table = QTableWidget()
        self.credentials_table.setColumnCount(4)
        self.credentials_table.setHorizontalHeaderLabels(["ID", "OMS ID", "Токен", "GLN"])
        
        # Первоначальное заполнение таблицы
        self.reload_credentials()
        
        layout.addWidget(self.credentials_table)
        
        # Кнопки управления учетными данными
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.on_add_credentials)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self.on_edit_credentials)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.on_delete_credentials)
        buttons_layout.addWidget(delete_button)
        
        layout.addLayout(buttons_layout)
    
    def reload_credentials(self, *args):
        """Обновить таблицу учетных данных в диалоге"""
        # Копируем данные из таблицы главного окна
        source_table = self.main_window.credentials_table
        self.credentials_table.setRowCount(source_table.rowCount())
        for row in range(source_table.rowCount()):
            for col in range(source_table.columnCount()):
                if source_table.item(row, col):
                    self.credentials_table.setItem(row, col, QTableWidgetItem(source_table.item(row, col).text()))
        self.credentials_table.resizeColumnsToContents()
    
    def on_add_credentials(self):
        """Обработчик нажатия кнопки добавления учетных данных в диалоге"""
        dialog = CredentialsDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            
            # Получаем выбранное подключение, если оно есть
            connection_id = None
            row = self.connections_table.currentRow()
            if row >= 0:
                connection_id = int(self.connections_table.item(row, 0).text())
            
            # Вызываем сигнал в главном окне
            self.main_window.add_credentials_signal.emit(data['omsid'], data['token'], data['gln'], connection_id)
    
    def on_edit_credentials(self):
        """Обработчик нажатия кнопки редактирования учетных данных в диалоге"""
        selected_rows = self.credentials_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите учетные данные для редактирования")
            return
        
        row = selected_rows[0].row()
        
        # Получаем данные из таблицы
        try:
            credentials_id = int(self.credentials_table.item(row, 0).text()) if self.credentials_table.item(row, 0) else 0
            omsid = self.credentials_table.item(row, 1).text() if self.credentials_table.item(row, 1) else ""
            token = self.credentials_table.item(row, 2).text() if self.credentials_table.item(row, 2) else ""
            gln = self.credentials_table.item(row, 3).text() if self.credentials_table.item(row, 3) else ""
            
            # Открываем диалог редактирования
            dialog = CredentialsDialog(self, {"omsid": omsid, "token": token, "gln": gln})
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                self.main_window.edit_credentials_signal.emit(credentials_id, data['omsid'], data['token'], data['gln'])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при редактировании учетных данных: {str(e)}")
    
    def on_delete_credentials(self):
        """Обработчик нажатия кнопки удаления учетных данных в диалоге"""
        selected_rows = self.credentials_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите учетные данные для удаления")
            return
        
        row = selected_rows[0].row()
        
        try:
            # Получаем ID учетных данных
            credentials_id = int(self.credentials_table.item(row, 0).text()) if self.credentials_table.item(row, 0) else 0
            
            # Запрашиваем подтверждение
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setText("Вы уверены, что хотите удалить эти учетные данные?")
            msg_box.setWindowTitle("Подтверждение удаления")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                # Вызываем сигнал удаления учетных данных
                self.main_window.delete_credentials_signal.emit(credentials_id)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при удалении учетных данных: {str(e)}")
    
    def create_general_settings_tab(self):
        """Создание вкладки общих настроек"""
        self.general_settings_tab = QWidget()
        layout = QVBoxLayout(self.general_settings_tab)
        
        # Пока вкладка пустая, добавляем заглушку
        layout.addWidget(QLabel("Общие настройки находятся в разработке"))

class UtilisationReportDialog(QDialog):
    """Диалог для создания отчета о нанесении"""
    
    def __init__(self, file_id, parent=None, controller=None):
        super().__init__(parent)
        self.file_id = file_id
        self.setWindowTitle("Отчет о нанесении")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Получаем данные о файле агрегации из контроллера
        self.parent_window = parent
        self.controller = controller  # Сохраняем ссылку на контроллер
        self.file_data = None
        
        # Создаем макет
        layout = QVBoxLayout(self)
        
        # Информация о файле
        file_info_layout = QFormLayout()
        self.file_name_label = QLabel("Загрузка...")
        self.product_label = QLabel("Загрузка...")
        self.codes_count_label = QLabel("Загрузка...")
        
        file_info_layout.addRow("Файл:", self.file_name_label)
        file_info_layout.addRow("Продукция:", self.product_label)
        file_info_layout.addRow("Количество кодов:", self.codes_count_label)
        
        layout.addLayout(file_info_layout)
        
        # Добавляем поля для ввода дополнительной информации
        additional_info_group = QGroupBox("Параметры отчета о нанесении")
        additional_info_layout = QFormLayout()
        
        # Срок годности
        self.expiration_date_edit = QDateEdit()
        self.expiration_date_edit.setCalendarPopup(True)
        # Устанавливаем текущую дату + 1 год
        import datetime
        future_date = datetime.datetime.now() + datetime.timedelta(days=365)
        self.expiration_date_edit.setDate(QDate(future_date.year, future_date.month, future_date.day))
        self.expiration_date_edit.setToolTip("Срок годности (может быть извлечен из поля DateExpiration файла агрегации)")
        additional_info_layout.addRow("Срок годности:", self.expiration_date_edit)
        
        # Номер производственной серии
        self.series_number_edit = QLineEdit("001")
        self.series_number_edit.setToolTip("Номер производственной серии (может быть извлечен из поля ClaimNumber файла агрегации)")
        additional_info_layout.addRow("Номер серии:", self.series_number_edit)
        
        # Тип использования
        self.usage_type_combo = QComboBox()
        
        # Устанавливаем только допустимые значения согласно API
        # По документации API, допустимые значения: PRINTED, VERIFIED
        self.usage_type_combo.addItem("Напечатан (PRINTED)", "PRINTED")
        self.usage_type_combo.addItem("Проверен (VERIFIED)", "VERIFIED")
        
        # Устанавливаем первый элемент по умолчанию
        self.usage_type_combo.setCurrentIndex(0)
        
        self.usage_type_combo.setToolTip("Тип использования кодов маркировки (допустимые значения: PRINTED, VERIFIED)")
        additional_info_layout.addRow("Тип использования:", self.usage_type_combo)
        
        # Добавляем информационную надпись
        info_label = QLabel("Примечание: Номер серии и срок годности могут быть заполнены автоматически из файла агрегации")
        info_label.setStyleSheet("color: blue; font-style: italic;")
        additional_info_layout.addRow("", info_label)
        
        additional_info_group.setLayout(additional_info_layout)
        layout.addWidget(additional_info_group)
        
        # Таблица для отображения кодов маркировки
        self.codes_table = QTableWidget()
        self.codes_table.setColumnCount(2)
        self.codes_table.setHorizontalHeaderLabels(["Код маркировки", "Включить в отчет"])
        self.codes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.codes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        # Индикатор загрузки
        self.loading_label = QLabel("Загрузка данных файла агрегации...")
        layout.addWidget(self.loading_label)
        
        layout.addWidget(QLabel("Выберите коды маркировки для включения в отчет:"))
        layout.addWidget(self.codes_table)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Выбрать все")
        self.select_all_button.clicked.connect(self.select_all_codes)
        button_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Снять выбор")
        self.deselect_all_button.clicked.connect(self.deselect_all_codes)
        button_layout.addWidget(self.deselect_all_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.submit_button = QPushButton("Отправить отчет")
        self.submit_button.clicked.connect(self.accept)
        button_layout.addWidget(self.submit_button)
        
        layout.addLayout(button_layout)
        
        # Загружаем данные файла
        self.load_file_data()
    
    def load_file_data(self):
        """Загрузка данных файла агрегации"""
        try:
            # Получаем данные из БД через контроллер
            from models.models import AggregationFile
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"Начинаем загрузку данных файла агрегации с ID={self.file_id}")
            
            # Проверяем, есть ли контроллер
            if not self.controller:
                logger.error("Отсутствует контроллер")
                QMessageBox.critical(self, "Ошибка", "Ошибка конфигурации: отсутствует контроллер")
                self.reject()
                return
                
            # Проверяем соединение с базой данных
            if not hasattr(self.controller, 'db') or not self.controller.db:
                logger.error("У контроллера отсутствует соединение с базой данных")
                QMessageBox.critical(self, "Ошибка", "Ошибка конфигурации: нет соединения с базой данных")
                self.reject()
                return
            
            # Получаем данные из контроллера
            try:
                # Получаем файл агрегации по ID через метод контроллера
                logger.info(f"Пробуем получить файл агрегации с ID={self.file_id} через метод контроллера")
                self.file_data = self.controller.get_aggregation_file_by_id(self.file_id)
                
                if self.file_data:
                    # Файл найден, проверяем наличие кодов маркировки
                    logger.info(f"Файл агрегации получен: {self.file_data.filename}")
                    
                    if not hasattr(self.file_data, 'marking_codes') or not self.file_data.marking_codes:
                        logger.warning(f"Файл агрегации не содержит кодов маркировки")
                        QMessageBox.warning(
                            self,
                            "Предупреждение",
                            "Файл агрегации не содержит кодов маркировки для отчета"
                        )
                    else:
                        logger.info(f"Количество кодов маркировки в файле: {len(self.file_data.marking_codes)}")
                    
                    # Обновляем UI
                    self.update_file_info()
                    return
                else:
                    logger.error(f"Файл агрегации с ID={self.file_id} не найден в базе данных")
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Не удалось получить данные файла агрегации с ID {self.file_id}"
                    )
                    self.reject()
                    return
            except Exception as e:
                logger.error(f"Ошибка при получении данных из контроллера: {str(e)}")
                logger.exception("Подробная трассировка ошибки:")
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось загрузить данные файла агрегации: {str(e)}"
                )
                self.reject()
                return
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных файла агрегации: {str(e)}")
            logger.exception("Подробная трассировка ошибки:")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить данные файла агрегации: {str(e)}"
            )
            self.reject()
    
    def update_file_info(self):
        """Обновление информации о файле и заполнение таблицы"""
        if not self.file_data:
            return
        
        # Обновляем метки с информацией о файле
        self.file_name_label.setText(self.file_data.filename)
        self.product_label.setText(self.file_data.product)
        self.codes_count_label.setText(str(len(self.file_data.marking_codes)))
        
        # Скрываем индикатор загрузки
        self.loading_label.hide()
        
        # Пробуем извлечь номер серии и срок годности из JSON-данных
        try:
            import json
            import logging
            logger = logging.getLogger(__name__)
            
            # Проверяем наличие JSON-содержимого
            if hasattr(self.file_data, 'json_content') and self.file_data.json_content:
                logger.info(f"Извлечение данных из JSON: {self.file_data.filename}")
                
                # Первая попытка - парсим JSON
                try:
                    json_data = json.loads(self.file_data.json_content)
                    logger.info(f"JSON успешно распарсен, ключи: {', '.join(json_data.keys())}")
                    
                    # Извлекаем номер серии (ищем в разных полях)
                    series_fields = ['ClaimNumber', 'SeriesNumber', 'Batch', 'BatchNumber']
                    for field in series_fields:
                        if field in json_data:
                            claim_number = json_data[field]
                            self.series_number_edit.setText(claim_number)
                            logger.info(f"Номер серии извлечен из поля {field}: {claim_number}")
                            break
                    
                    # Извлекаем срок годности (ищем в разных полях)
                    date_fields = ['DateExpiration', 'ExpirationDate', 'ExpiryDate', 'BestBefore']
                    for field in date_fields:
                        if field in json_data:
                            date_expiration = json_data[field]
                            logger.info(f"Найдено поле с датой {field}: {date_expiration}")
                            
                            # Проверяем различные форматы даты
                            date_formats = [
                                '%Y-%m-%d',       # 2023-12-31
                                '%d.%m.%Y',       # 31.12.2023
                                '%Y/%m/%d',       # 2023/12/31
                                '%d/%m/%Y',       # 31/12/2023
                                '%m/%d/%Y',       # 12/31/2023
                                '%Y-%m-%dT%H:%M:%S',  # ISO формат
                                '%Y-%m-%dT%H:%M:%S.%fZ'  # ISO формат с миллисекундами
                            ]
                            
                            expiration_date = None
                            for date_format in date_formats:
                                try:
                                    import datetime
                                    expiration_date = datetime.datetime.strptime(date_expiration, date_format)
                                    logger.info(f"Срок годности извлечен из поля {field}: {date_expiration} (формат: {date_format})")
                                    break
                                except ValueError:
                                    continue
                            
                            if expiration_date:
                                self.expiration_date_edit.setDate(QDate(expiration_date.year, expiration_date.month, expiration_date.day))
                                break
                            else:
                                logger.warning(f"Невозможно парсить дату из {field}: {date_expiration}")
                except json.JSONDecodeError as je:
                    logger.error(f"Ошибка парсинга JSON: {str(je)}")
                
                # Вторая попытка - если JSON не распарсился или не нашли нужные поля, 
                # пробуем извлечь значения с помощью регулярных выражений
                if not self.series_number_edit.text() or self.series_number_edit.text() == "001":
                    import re
                    
                    # Ищем номер серии
                    series_patterns = [
                        r'ClaimNumber["\s:=]+([^"\s,}]+)',
                        r'SeriesNumber["\s:=]+([^"\s,}]+)',
                        r'Batch["\s:=]+([^"\s,}]+)',
                        r'BatchNumber["\s:=]+([^"\s,}]+)'
                    ]
                    
                    for pattern in series_patterns:
                        series_match = re.search(pattern, self.file_data.json_content)
                        if series_match:
                            series = series_match.group(1).strip('"\'')
                            self.series_number_edit.setText(series)
                            logger.info(f"Номер серии извлечен с помощью regex: {series}")
                            break
                
                # Ищем дату с помощью regex, если не нашли раньше
                date_regex = r'(?:DateExpiration|ExpirationDate|ExpiryDate|BestBefore)["\s:=]+"?([^"\s,}]+)"?'
                date_match = re.search(date_regex, self.file_data.json_content)
                if date_match:
                    date_str = date_match.group(1)
                    logger.info(f"Дата извлечена с помощью regex: {date_str}")
                    
                    # Парсим дату с помощью regex
                    date_parts = re.findall(r'\d+', date_str)
                    if len(date_parts) >= 3:
                        try:
                            # Предполагаем разные форматы: год-месяц-день или день-месяц-год
                            # Если первое число > 31, скорее всего это год
                            if int(date_parts[0]) > 31:
                                year = int(date_parts[0])
                                month = int(date_parts[1])
                                day = int(date_parts[2])
                            else:
                                # Иначе это день-месяц-год
                                day = int(date_parts[0])
                                month = int(date_parts[1])
                                year = int(date_parts[2])
                                
                                # Если год двузначный, добавляем 2000
                                if year < 100:
                                    year += 2000
                            
                            # Проверяем валидность даты
                            if 1 <= month <= 12 and 1 <= day <= 31 and year > 2000:
                                from PyQt6.QtCore import QDate
                                self.expiration_date_edit.setDate(QDate(year, month, day))
                                logger.info(f"Срок годности извлечен из файла с помощью regex: {year}-{month}-{day}")
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Ошибка при парсинге даты: {str(e)}")
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из JSON: {str(e)}")
            logger.exception("Подробная трассировка ошибки:")
        
        # Заполняем таблицу кодами маркировки
        self.codes_table.setRowCount(len(self.file_data.marking_codes))
        
        for i, code in enumerate(self.file_data.marking_codes):
            # Код маркировки
            self.codes_table.setItem(i, 0, QTableWidgetItem(code))
            
            # Чекбокс для выбора
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked)
            self.codes_table.setItem(i, 1, checkbox)
        
        self.codes_table.resizeColumnsToContents()
    
    def select_all_codes(self):
        """Выбрать все коды маркировки"""
        for i in range(self.codes_table.rowCount()):
            self.codes_table.item(i, 1).setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_codes(self):
        """Снять выбор со всех кодов маркировки"""
        for i in range(self.codes_table.rowCount()):
            self.codes_table.item(i, 1).setCheckState(Qt.CheckState.Unchecked)
    
    def get_report_data(self):
        """Получение данных отчета для отправки"""
        # Собираем выбранные коды маркировки
        selected_codes = []
        for i in range(self.codes_table.rowCount()):
            if self.codes_table.item(i, 1).checkState() == Qt.CheckState.Checked:
                code = self.codes_table.item(i, 0).text()
                # Заменяем текстовое представление [GS] на реальный символ GS (код 29)
                code = code.replace('[GS]', '\x1d')
                selected_codes.append(code)
        
        # Получаем срок годности из поля ввода
        expiration_date = self.expiration_date_edit.date().toString('yyyy-MM-dd')
        
        # Получаем номер серии из поля ввода
        series_number = self.series_number_edit.text().strip()
        if not series_number:
            series_number = "001"  # Значение по умолчанию
        
        # Получаем тип использования из выпадающего списка
        # Сначала пытаемся получить код из данных элемента
        usage_type = self.usage_type_combo.currentData()
        # Если данные не установлены, используем текст
        if not usage_type:
            usage_type = self.usage_type_combo.currentText()
        
        # Получаем omsId из текущих учетных данных через контроллер
        omsId = ""
        try:
            if self.controller and hasattr(self.controller, 'db'):
                credentials = self.controller.db.get_credentials()
                if credentials and len(credentials) > 0:
                    omsId = credentials[0].omsid
                    logging.getLogger(__name__).info(f"Получен omsId для отчета: {omsId}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка при получении omsId: {str(e)}")
            
        # Если omsId не удалось получить из БД, пытаемся получить из api_client
        if not omsId and self.controller and hasattr(self.controller, 'api_client'):
            omsId = self.controller.api_client.omsid
            if omsId:
                logging.getLogger(__name__).info(f"Получен omsId из API-клиента: {omsId}")
        
        # Формируем структуру данных для отправки отчета в формате API
        report_data = {
            "sntins": selected_codes,
            # Добавляем обязательные поля согласно документации
            "expirationDate": expiration_date,
            "seriesNumber": series_number,
            "usageType": usage_type,
            "omsId": omsId  # Добавляем omsId в отчет
        }
        
        # Если не удалось получить omsId, показываем предупреждение пользователю
        if not omsId:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не удалось получить идентификатор СУЗ (omsId). Отчет может быть отклонен API. "
                "Проверьте настройки учетных данных."
            )
            logging.getLogger(__name__).warning("omsId не был добавлен в отчет об использовании")
        
        return report_data