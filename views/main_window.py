from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                            QMessageBox, QLineEdit, QComboBox, QTabWidget, QSplitter, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from .dialogs import ConnectionDialog, CredentialsDialog, NomenclatureDialog
import logging
import datetime
import json
from models.models import Extension, Nomenclature, EmissionType, Country

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    # Сигналы для работы с заказами
    add_order_signal = pyqtSignal(str, str)
    ping_signal = pyqtSignal()
    get_orders_signal = pyqtSignal()
    get_report_signal = pyqtSignal()
    get_version_signal = pyqtSignal()  # Сигнал для запроса версии СУЗ и API
    get_orders_status_signal = pyqtSignal()  # Сигнал для получения статуса заказов
    create_emission_order_signal = pyqtSignal(dict)  # Сигнал для создания заказа на эмиссию кодов
    
    # Сигналы для работы с подключениями
    add_connection_signal = pyqtSignal(str, str)
    edit_connection_signal = pyqtSignal(int, str, str)
    delete_connection_signal = pyqtSignal(int)
    set_active_connection_signal = pyqtSignal(int)
    
    # Сигналы для работы с учетными данными
    add_credentials_signal = pyqtSignal(str, str, int)
    edit_credentials_signal = pyqtSignal(int, str, str)
    delete_credentials_signal = pyqtSignal(int)
    
    # Сигналы для работы с номенклатурой
    add_nomenclature_signal = pyqtSignal(str, str, str)
    edit_nomenclature_signal = pyqtSignal(int, str, str, str)
    delete_nomenclature_signal = pyqtSignal(int)
    
    # Сигналы для работы с расширениями API
    set_active_extension_signal = pyqtSignal(int)
    
    # Сигналы для работы с логами API
    load_api_logs_signal = pyqtSignal()
    get_api_log_details_signal = pyqtSignal(int, object, object) # log_id, callback для request, callback для response
    export_api_descriptions_signal = pyqtSignal()  # Сигнал для экспорта описаний API в файл
    
    # Сигналы для контроллера
    load_countries_signal = pyqtSignal()
    
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
        self.create_connections_tab()
        self.create_credentials_tab()
        self.create_nomenclature_tab()
        self.create_extensions_tab()
        self.create_api_logs_tab()  # Новая вкладка для логов API
        self.create_countries_tab()  # Новая вкладка для списка стран
        
        # Добавляем вкладки в виджет
        self.tabs.addTab(self.orders_tab, "Заказы")
        self.tabs.addTab(self.connections_tab, "Подключения")
        self.tabs.addTab(self.credentials_tab, "Учетные данные")
        self.tabs.addTab(self.nomenclature_tab, "Номенклатура")
        self.tabs.addTab(self.extensions_tab, "Виды продукции")
        self.tabs.addTab(self.api_logs_tab, "Логи API")
        self.tabs.addTab(self.countries_tab, "Страны")
    
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
        refresh_button.clicked.connect(self.load_api_logs_signal.emit)
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
    
    def create_extensions_tab(self):
        """Создание вкладки видов продукции (расширений API)"""
        self.extensions_tab = QWidget()
        layout = QVBoxLayout(self.extensions_tab)
        
        # Таблица расширений
        self.extensions_table = QTableWidget()
        self.extensions_table.setColumnCount(4)
        self.extensions_table.setHorizontalHeaderLabels(["ID", "Код", "Наименование", "Активно"])
        layout.addWidget(self.extensions_table)
        
        # Кнопки для работы с расширениями
        buttons_layout = QHBoxLayout()
        
        set_active_button = QPushButton("Сделать активным")
        set_active_button.clicked.connect(self.on_set_active_extension_clicked)
        buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(buttons_layout)
    
    def on_set_active_extension_clicked(self):
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
            self.extensions_table.setItem(row, 1, QTableWidgetItem(extension.code))
            self.extensions_table.setItem(row, 2, QTableWidgetItem(extension.name))
            self.extensions_table.setItem(row, 3, QTableWidgetItem("Да" if extension.is_active else "Нет"))
    
    def on_add_order_clicked(self):
        """Обработчик нажатия кнопки добавления заказа"""
        order_number = self.order_number_input.text()
        status = self.order_status_input.text()
        if order_number and status:
            self.add_order_signal.emit(order_number, status)
            self.order_number_input.clear()
            self.order_status_input.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
    
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
            self.add_credentials_signal.emit(data['omsid'], data['token'], connection_id)
    
    def on_edit_credentials_clicked(self):
        """Обработчик нажатия кнопки редактирования учетных данных"""
        row = self.credentials_table.currentRow()
        if row >= 0:
            credentials_id = int(self.credentials_table.item(row, 0).text())
            omsid = self.credentials_table.item(row, 2).text()
            token = self.credentials_table.item(row, 3).text()
            
            dialog = CredentialsDialog(self)
            # Заполняем поля текущими значениями
            dialog.omsid_input.setText(omsid)
            dialog.token_input.setText(token)
            
            if dialog.exec():
                data = dialog.get_data()
                self.edit_credentials_signal.emit(credentials_id, data['omsid'], data['token'])
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите учетные данные для редактирования")
    
    def on_delete_credentials_clicked(self):
        """Обработчик нажатия кнопки удаления учетных данных"""
        row = self.credentials_table.currentRow()
        if row >= 0:
            credentials_id = int(self.credentials_table.item(row, 0).text())
            self.delete_credentials_signal.emit(credentials_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите учетные данные для удаления")
    
    def on_add_nomenclature_clicked(self):
        """Обработчик нажатия кнопки добавления номенклатуры"""
        # Получаем список расширений API перед открытием диалога
        extensions = []
        for row in range(self.extensions_table.rowCount()):
            extension_id = int(self.extensions_table.item(row, 0).text())
            extension_code = self.extensions_table.item(row, 1).text()
            extension_name = self.extensions_table.item(row, 2).text()
            is_active = self.extensions_table.item(row, 3).text() == "Да"
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
            for row in range(self.extensions_table.rowCount()):
                extension_id = int(self.extensions_table.item(row, 0).text())
                extension_code = self.extensions_table.item(row, 1).text()
                extension_name = self.extensions_table.item(row, 2).text()
                is_active = self.extensions_table.item(row, 3).text() == "Да"
                extensions.append(Extension(extension_id, extension_code, extension_name, is_active))
            
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
            self.delete_nomenclature_signal.emit(nomenclature_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите номенклатуру для удаления")
    
    def update_orders_table(self, orders):
        """Обновление таблицы заказов"""
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.order_number))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order.status))
            self.orders_table.setItem(row, 3, QTableWidgetItem(str(order.created_at)))
    
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
            
            # Отображаем имя подключения, если оно есть
            connection_name = cred.connection.name if cred.connection else "Не указано"
            self.credentials_table.setItem(row, 1, QTableWidgetItem(connection_name))
            
            self.credentials_table.setItem(row, 2, QTableWidgetItem(cred.omsid))
            self.credentials_table.setItem(row, 3, QTableWidgetItem(cred.token))
    
    def update_nomenclature_table(self, nomenclature):
        """Обновление таблицы номенклатуры"""
        self.nomenclature_table.setRowCount(len(nomenclature))
        for row, item in enumerate(nomenclature):
            self.nomenclature_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.nomenclature_table.setItem(row, 1, QTableWidgetItem(item.name))
            self.nomenclature_table.setItem(row, 2, QTableWidgetItem(item.gtin))
            self.nomenclature_table.setItem(row, 3, QTableWidgetItem(item.product_group))
    
    def show_message(self, title, message):
        """Показать сообщение"""
        QMessageBox.information(self, title, message)

    def create_orders_tab(self):
        """Создание вкладки заказов"""
        self.orders_tab = QWidget()
        layout = QVBoxLayout(self.orders_tab)
        
        # Таблица заказов
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Номер заказа", "Статус", "Дата создания"])
        layout.addWidget(self.orders_table)
        
        # Кнопки для работы с API
        api_layout = QHBoxLayout()
        self.ping_button = QPushButton("Проверить API")
        self.ping_button.clicked.connect(self.on_ping_clicked)
        self.get_orders_button = QPushButton("Получить заказы")
        self.get_orders_button.clicked.connect(self.on_get_orders_clicked)
        self.get_report_button = QPushButton("Получить отчет")
        self.get_report_button.clicked.connect(self.on_get_report_clicked)
        self.get_version_button = QPushButton("Получить версию СУЗ и API")
        self.get_version_button.clicked.connect(self.on_get_version_clicked)
        self.get_orders_status_button = QPushButton("Получить статус заказов")
        self.get_orders_status_button.clicked.connect(self.on_get_orders_status_clicked)
        self.create_emission_order_button = QPushButton("Создать заказ на эмиссию КМ")
        self.create_emission_order_button.clicked.connect(self.on_create_emission_order_clicked)
        
        api_layout.addWidget(self.ping_button)
        api_layout.addWidget(self.get_orders_button)
        api_layout.addWidget(self.get_report_button)
        api_layout.addWidget(self.get_version_button)
        api_layout.addWidget(self.get_orders_status_button)
        api_layout.addWidget(self.create_emission_order_button)
        
        layout.addLayout(api_layout)

    def create_connections_tab(self):
        """Создание вкладки подключений"""
        self.connections_tab = QWidget()
        layout = QVBoxLayout(self.connections_tab)
        
        # Таблица подключений
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(4)
        self.connections_table.setHorizontalHeaderLabels(["ID", "Название", "URL", "Активно"])
        layout.addWidget(self.connections_table)
        
        # Кнопки для работы с подключениями
        buttons_layout = QHBoxLayout()
        add_connection_button = QPushButton("Добавить подключение")
        add_connection_button.clicked.connect(self.on_add_connection_clicked)
        buttons_layout.addWidget(add_connection_button)
        
        edit_connection_button = QPushButton("Редактировать")
        edit_connection_button.clicked.connect(self.on_edit_connection_clicked)
        buttons_layout.addWidget(edit_connection_button)
        
        delete_connection_button = QPushButton("Удалить")
        delete_connection_button.clicked.connect(self.on_delete_connection_clicked)
        buttons_layout.addWidget(delete_connection_button)
        
        set_active_button = QPushButton("Сделать активным")
        set_active_button.clicked.connect(self.on_set_active_connection_clicked)
        buttons_layout.addWidget(set_active_button)
        
        layout.addLayout(buttons_layout)

    def create_credentials_tab(self):
        """Создание вкладки учетных данных"""
        self.credentials_tab = QWidget()
        layout = QVBoxLayout(self.credentials_tab)
        
        # Таблица учетных данных
        self.credentials_table = QTableWidget()
        self.credentials_table.setColumnCount(4)
        self.credentials_table.setHorizontalHeaderLabels(["ID", "Подключение", "OMSID", "Token"])
        layout.addWidget(self.credentials_table)
        
        # Кнопки для работы с учетными данными
        buttons_layout = QHBoxLayout()
        add_credentials_button = QPushButton("Добавить учетные данные")
        add_credentials_button.clicked.connect(self.on_add_credentials_clicked)
        buttons_layout.addWidget(add_credentials_button)
        
        edit_credentials_button = QPushButton("Редактировать")
        edit_credentials_button.clicked.connect(self.on_edit_credentials_clicked)
        buttons_layout.addWidget(edit_credentials_button)
        
        delete_credentials_button = QPushButton("Удалить")
        delete_credentials_button.clicked.connect(self.on_delete_credentials_clicked)
        buttons_layout.addWidget(delete_credentials_button)
        
        layout.addLayout(buttons_layout)

    def create_nomenclature_tab(self):
        """Создание вкладки номенклатуры"""
        self.nomenclature_tab = QWidget()
        layout = QVBoxLayout(self.nomenclature_tab)
        
        # Таблица номенклатуры
        self.nomenclature_table = QTableWidget()
        self.nomenclature_table.setColumnCount(4)
        self.nomenclature_table.setHorizontalHeaderLabels(["ID", "Наименование", "GTIN", "Товарная группа"])
        layout.addWidget(self.nomenclature_table)
        
        # Кнопки для работы с номенклатурой
        buttons_layout = QHBoxLayout()
        add_nomenclature_button = QPushButton("Добавить номенклатуру")
        add_nomenclature_button.clicked.connect(self.on_add_nomenclature_clicked)
        buttons_layout.addWidget(add_nomenclature_button)
        
        edit_nomenclature_button = QPushButton("Редактировать")
        edit_nomenclature_button.clicked.connect(self.on_edit_nomenclature_clicked)
        buttons_layout.addWidget(edit_nomenclature_button)
        
        delete_nomenclature_button = QPushButton("Удалить")
        delete_nomenclature_button.clicked.connect(self.on_delete_nomenclature_clicked)
        buttons_layout.addWidget(delete_nomenclature_button)
        
        layout.addLayout(buttons_layout)

    def on_create_emission_order_clicked(self):
        """Обработчик нажатия кнопки создания заказа на эмиссию КМ"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from .dialogs import EmissionOrderDialog
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
            code_item = self.extensions_table.item(row, 1)
            name_item = self.extensions_table.item(row, 2)
            is_active_item = self.extensions_table.item(row, 3)
            
            if id_item and code_item and name_item and is_active_item:
                from models.models import Extension
                extension = Extension(
                    int(id_item.text()),
                    code_item.text(),
                    name_item.text(),
                    is_active_item.text() == "Да"
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
        
        # Получаем данные о типах эмиссии из контроллера
        # Но поскольку нет прямого доступа к базе данных, создаем типы эмиссии вручную
        emission_types = [
            EmissionType(1, "PRODUCTION", "Производство в Казахстане", None),
            EmissionType(2, "IMPORT", "Ввезен в Казахстан (Импорт)", None),
            EmissionType(3, "REMAINS", "Маркировка остатков", "shoes"),
            EmissionType(4, "COMMISSION", "Принят на коммиссию от физ.лица", "shoes"),
            EmissionType(5, "REMARK", "Перемаркировка", None)
        ]
        
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
        self.countries_table.setHorizontalHeaderLabels(["ID", "Код страны", "Название"])
        layout.addWidget(self.countries_table)
        
        # Кнопка обновления
        refresh_button = QPushButton("Обновить список стран")
        refresh_button.clicked.connect(self.load_countries_signal.emit)
        layout.addWidget(refresh_button)
    
    def update_countries_table(self, countries):
        """Обновление таблицы стран"""
        self.countries_table.setRowCount(len(countries))
        for row, country in enumerate(countries):
            self.countries_table.setItem(row, 0, QTableWidgetItem(str(country.id)))
            self.countries_table.setItem(row, 1, QTableWidgetItem(country.code))
            self.countries_table.setItem(row, 2, QTableWidgetItem(country.name))
        self.countries_table.resizeColumnsToContents() 