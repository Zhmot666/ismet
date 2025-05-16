from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                            QMessageBox, QComboBox, QGroupBox, QFormLayout, QSpinBox,
                            QTextEdit, QDateEdit, QDialogButtonBox, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QPixmap
import re
import os

class BaseDialog(QDialog):
    """Базовый класс для диалоговых окон"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Диалоговое окно")
        self.setModal(True)
        
    def show_error(self, message):
        """Показать сообщение об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
    
    def show_success(self, message):
        """Показать сообщение об успехе"""
        QMessageBox.information(self, "Успех", message)

class ConnectionDialog(BaseDialog):
    """Диалог для работы с подключениями"""
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.connection = connection
        self.setWindowTitle("Подключение" if connection else "Новое подключение")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Поле для названия
        name_layout = QHBoxLayout()
        name_label = QLabel("Название:")
        self.name_input = QLineEdit()
        if self.connection:
            self.name_input.setText(self.connection.name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Поле для URL
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        if self.connection:
            self.url_input.setText(self.connection.url)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Получить данные из формы"""
        return {
            'name': self.name_input.text(),
            'url': self.url_input.text()
        }

class CredentialsDialog(BaseDialog):
    """Диалог для работы с учетными данными"""
    def __init__(self, parent=None, credentials=None):
        super().__init__(parent)
        self.credentials = credentials
        self.setWindowTitle("Учетные данные" if credentials else "Новые учетные данные")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Поле для OMSID
        omsid_layout = QHBoxLayout()
        omsid_label = QLabel("OMSID:")
        self.omsid_input = QLineEdit()
        if self.credentials:
            # Проверяем, является ли credentials словарем
            if isinstance(self.credentials, dict):
                # Если это словарь, используем метод get для безопасного доступа к ключам
                self.omsid_input.setText(self.credentials.get('omsid', ''))
            else:
                # Если это объект, то используем атрибуты
                self.omsid_input.setText(self.credentials.omsid)
        omsid_layout.addWidget(omsid_label)
        omsid_layout.addWidget(self.omsid_input)
        layout.addLayout(omsid_layout)
        
        # Поле для Token
        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        self.token_input = QLineEdit()
        if self.credentials:
            # Проверяем, является ли credentials словарем
            if isinstance(self.credentials, dict):
                # Если это словарь, используем метод get для безопасного доступа к ключам
                self.token_input.setText(self.credentials.get('token', ''))
            else:
                # Если это объект, то используем атрибуты
                self.token_input.setText(self.credentials.token)
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)
        
        # Поле для GLN
        gln_layout = QHBoxLayout()
        gln_label = QLabel("GLN (factoryId):")
        self.gln_input = QLineEdit()
        if self.credentials:
            # Проверяем, является ли credentials словарем
            if isinstance(self.credentials, dict):
                # Если это словарь, используем метод get для безопасного доступа к ключам
                self.gln_input.setText(self.credentials.get('gln', ''))
            else:
                # Если это объект, то используем атрибуты
                self.gln_input.setText(self.credentials.gln)
        gln_layout.addWidget(gln_label)
        gln_layout.addWidget(self.gln_input)
        layout.addLayout(gln_layout)
        
        # Поле для ИНН
        inn_layout = QHBoxLayout()
        inn_label = QLabel("ИНН (participantId):")
        self.inn_input = QLineEdit()
        if self.credentials:
            # Проверяем, является ли credentials словарем
            if isinstance(self.credentials, dict):
                # Если это словарь, используем метод get для безопасного доступа к ключам
                self.inn_input.setText(self.credentials.get('inn', ''))
            else:
                # Если это объект, то используем атрибуты
                self.inn_input.setText(self.credentials.inn)
        inn_layout.addWidget(inn_label)
        inn_layout.addWidget(self.inn_input)
        layout.addLayout(inn_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Получить данные из формы"""
        return {
            'omsid': self.omsid_input.text(),
            'token': self.token_input.text(),
            'gln': self.gln_input.text(),
            'inn': self.inn_input.text()
        }

class NomenclatureDialog(BaseDialog):
    """Диалог для работы с номенклатурой"""
    def __init__(self, parent=None, nomenclature=None, extensions=None):
        super().__init__(parent)
        self.nomenclature = nomenclature
        self.extensions = extensions or []
        self.setWindowTitle("Номенклатура" if nomenclature else "Новая номенклатура")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Поле для наименования
        name_layout = QHBoxLayout()
        name_label = QLabel("Наименование:")
        self.name_input = QLineEdit()
        if self.nomenclature:
            self.name_input.setText(self.nomenclature.name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Поле для GTIN
        gtin_layout = QHBoxLayout()
        gtin_label = QLabel("GTIN:")
        self.gtin_input = QLineEdit()
        if self.nomenclature:
            self.gtin_input.setText(self.nomenclature.gtin)
        gtin_layout.addWidget(gtin_label)
        gtin_layout.addWidget(self.gtin_input)
        layout.addLayout(gtin_layout)
        
        # Выпадающий список для товарной группы
        product_group_layout = QHBoxLayout()
        product_group_label = QLabel("Товарная группа:")
        self.product_group_combo = QComboBox()
        
        # Добавляем пустой элемент
        self.product_group_combo.addItem("-- Выберите товарную группу --", "")
        
        # Добавляем расширения API как опции
        for extension in self.extensions:
            self.product_group_combo.addItem(extension.name, extension.code)
        
        # Устанавливаем текущее значение, если номенклатура существует
        if self.nomenclature and hasattr(self.nomenclature, 'product_group') and self.nomenclature.product_group:
            # Ищем индекс значения в комбобоксе
            index = self.product_group_combo.findData(self.nomenclature.product_group)
            if index >= 0:
                self.product_group_combo.setCurrentIndex(index)
        
        product_group_layout.addWidget(product_group_label)
        product_group_layout.addWidget(self.product_group_combo)
        layout.addLayout(product_group_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Получить данные из формы"""
        return {
            'name': self.name_input.text(),
            'gtin': self.gtin_input.text(),
            'product_group': self.product_group_combo.currentData()
        }

class GetKMDialog(BaseDialog):
    """Диалог для выбора параметров получения КМ из заказа"""
    def __init__(self, parent=None, order_id=None, gtins=None):
        super().__init__(parent)
        self.order_id = order_id
        self.gtins = gtins or []
        self.setWindowTitle(f"Получение КМ из заказа {order_id}")
        self.resize(400, 200)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Информационное сообщение
        info_label = QLabel(f"Получение кодов маркировки из заказа {self.order_id}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        description_label = QLabel("Выберите GTIN товара и укажите количество кодов для получения.\n"
                                  "Максимальное количество кодов в одном запросе: 150000.")
        description_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(description_label)
        
        # Форма ввода параметров
        form_layout = QFormLayout()
        
        # Выбор GTIN
        self.gtin_combo = QComboBox()
        for gtin in self.gtins:
            self.gtin_combo.addItem(gtin, gtin)
        form_layout.addRow("GTIN:", self.gtin_combo)
        
        # Поле для ввода количества кодов
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(150000)
        self.quantity_spin.setValue(1000)  # По умолчанию 1000 кодов
        form_layout.addRow("Количество КМ:", self.quantity_spin)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("Получить")
        ok_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def validate_and_accept(self):
        """Валидация введённых параметров и закрытие диалога"""
        if not self.gtin_combo.currentText():
            self.show_error("Необходимо выбрать GTIN товара")
            return
            
        if self.quantity_spin.value() <= 0:
            self.show_error("Количество кодов должно быть больше 0")
            return
            
        if self.quantity_spin.value() > 150000:
            self.show_error("Максимальное количество кодов в одном запросе: 150000")
            return
            
        self.accept()
    
    def get_data(self):
        """Получить данные из формы"""
        return {
            'gtin': self.gtin_combo.currentText(),
            'quantity': self.quantity_spin.value()
        }

class DisplayCodesDialog(QDialog):
    """Диалог для отображения и экспорта кодов маркировки"""
    
    def __init__(self, parent, order_id, gtin, codes):
        """Инициализация диалога для отображения кодов маркировки
        
        Args:
            parent: Родительский виджет
            order_id (str): ID заказа
            gtin (str): GTIN товара
            codes (List[str]): Список кодов маркировки
        """
        super().__init__(parent)
        self.setWindowTitle(f"Коды маркировки для заказа {order_id} (GTIN: {gtin})")
        self.resize(600, 400)
        
        self.order_id = order_id
        self.gtin = gtin
        self.codes = codes
        
        layout = QVBoxLayout(self)
        
        # Информация о кодах
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Количество кодов: {len(codes)}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Обрабатываем коды для отображения, заменяя символы GS1 на понятное представление
        display_codes = []
        for code in codes:
            # Заменяем символ GS1 на видимое текстовое представление для отображения
            display_code = code.replace('\u001d', '[GS]')
            display_codes.append(display_code)
        
        # Текстовое поле с кодами
        self.codes_text = QTextEdit()
        self.codes_text.setReadOnly(True)
        self.codes_text.setText("\n".join(display_codes))
        layout.addWidget(self.codes_text)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        # Кнопка копирования в буфер обмена
        copy_button = QPushButton("Копировать в буфер обмена")
        copy_button.clicked.connect(self.copy_to_clipboard)
        buttons_layout.addWidget(copy_button)
        
        # Кнопка экспорта в файл
        export_button = QPushButton("Экспортировать в файл")
        export_button.clicked.connect(self.export_to_file)
        buttons_layout.addWidget(export_button)
        
        layout.addLayout(buttons_layout)
        
        # Добавляем информационное сообщение о символах GS1
        info_label = QLabel("Примечание: символы GS1 (Control Character 29) отображаются как [GS], но при экспорте или копировании будут восстановлены оригинальные символы.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Стандартные кнопки диалога
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def copy_to_clipboard(self):
        """Копирование кодов в буфер обмена"""
        from PyQt6.QtWidgets import QApplication
        
        try:
            # Восстанавливаем реальные символы GS1 перед копированием в буфер обмена
            processed_codes = []
            for code in self.codes:
                # Проверяем наличие текстового представления символа GS1
                if '[GS]' in code:
                    # Заменяем текстовое представление на фактический символ GS1 (ASCII 29, \u001d)
                    processed_code = code.replace('[GS]', '\u001d')
                else:
                    processed_code = code
                processed_codes.append(processed_code)
            
            # Копируем в буфер обмена
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(processed_codes))
            QMessageBox.information(self, "Информация", "Коды скопированы в буфер обмена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать коды в буфер обмена: {str(e)}")
    
    def export_to_file(self):
        """Экспорт кодов в файл"""
        # Запрашиваем имя файла для сохранения
        default_filename = f"codes_{self.order_id}_{self.gtin}.txt"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Экспорт кодов", default_filename, "Текстовые файлы (*.txt)"
        )
        
        if not filepath:
            return
        
        try:
            # Восстанавливаем реальные символы GS1 перед записью в файл
            processed_codes = []
            for code in self.codes:
                # Проверяем наличие текстового представления символа GS1
                if '[GS]' in code:
                    # Заменяем текстовое представление на фактический символ GS1 (ASCII 29, \u001d)
                    processed_code = code.replace('[GS]', '\u001d')
                else:
                    processed_code = code
                processed_codes.append(processed_code)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(processed_codes))
            QMessageBox.information(self, "Информация", f"Коды успешно экспортированы в файл: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")

class EmissionOrderDialog(QDialog):
    """Диалог для создания заказа на эмиссию кодов маркировки"""
    def __init__(self, parent=None, nomenclatures=None, extensions=None, emission_types=None, countries=None):
        super().__init__(parent)
        self.nomenclatures = nomenclatures or []
        self.extensions = extensions or []
        self.emission_types = emission_types or []
        self.countries = countries or []
        self.current_extension_code = None
        
        self.setWindowTitle("Создание заказа на эмиссию кодов маркировки")
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Выбор расширения API (категории продукции)
        extension_layout = QHBoxLayout()
        extension_label = QLabel("Расширение API:")
        self.extension_combo = QComboBox()
        for extension in self.extensions:
            self.extension_combo.addItem(extension.name, extension.code)
            if extension.is_active:
                self.extension_combo.setCurrentIndex(self.extension_combo.count() - 1)
                self.current_extension_code = extension.code
        
        self.extension_combo.currentIndexChanged.connect(self.on_extension_changed)
        extension_layout.addWidget(extension_label)
        extension_layout.addWidget(self.extension_combo)
        layout.addLayout(extension_layout)
        
        # Информация о продукте
        product_group = QGroupBox("Информация о продукте")
        product_layout = QFormLayout(product_group)
        
        # GTIN
        gtin_layout = QHBoxLayout()
        self.gtin_combo = QComboBox()
        self.gtin_combo.setEditable(True)
        for nomenclature in self.nomenclatures:
            self.gtin_combo.addItem(f"{nomenclature.name} ({nomenclature.gtin})", nomenclature.gtin)
        
        self.gtin_combo.setCurrentText("")
        gtin_layout.addWidget(self.gtin_combo)
        product_layout.addRow("GTIN товара:", gtin_layout)
        
        # Количество КМ
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 150000)
        self.quantity_input.setValue(100)
        product_layout.addRow("Количество кодов:", self.quantity_input)
        
        # Тип серийного номера
        self.serial_type_combo = QComboBox()
        self.serial_type_combo.addItem("Оператором (OPERATOR)", "OPERATOR")
        self.serial_type_combo.addItem("Собственная генерация (SELF_MADE)", "SELF_MADE")
        self.serial_type_combo.currentIndexChanged.connect(self.on_serial_type_changed)
        product_layout.addRow("Тип серийного номера:", self.serial_type_combo)
        
        # Серийные номера (для SELF_MADE)
        self.serial_numbers_input = QTextEdit()
        self.serial_numbers_input.setPlaceholderText("Введите серийные номера, по одному в строке")
        self.serial_numbers_input.setVisible(False)
        product_layout.addRow("Серийные номера:", self.serial_numbers_input)
        
        # ID шаблона
        self.template_id_input = QSpinBox()
        self.template_id_input.setRange(1, 1000)
        self.template_id_input.setValue(5)
        product_layout.addRow("ID шаблона КМ:", self.template_id_input)
        
        layout.addWidget(product_group)
        
        # Группа обязательных полей для всех типов заказов
        common_group = QGroupBox("Обязательная информация")
        common_layout = QFormLayout(common_group)
        
        # ID производства (factoryId) - обязательное поле для всех типов заказов
        self.factory_id_input = QLineEdit()
        common_layout.addRow("ID производства (factoryId)*:", self.factory_id_input)
        
        # Страна производителя - обязательное поле для всех типов заказов
        self.factory_country_combo = QComboBox()
        for country in self.countries:
            self.factory_country_combo.addItem(country.name, country.code)
        
        # Установка Беларуси по умолчанию для страны производителя
        default_factory_country_idx = self.factory_country_combo.findData("BY")
        if default_factory_country_idx >= 0:
            self.factory_country_combo.setCurrentIndex(default_factory_country_idx)
        
        common_layout.addRow("Страна производителя*:", self.factory_country_combo)
        
        # Способ выпуска товаров в оборот - обязательное поле для всех типов
        self.release_method_combo = QComboBox()
        common_layout.addRow("Способ выпуска товаров*:", self.release_method_combo)
        
        layout.addWidget(common_group)
        
        # Информация для фармацевтической промышленности
        self.pharma_group = QGroupBox("Информация для фармацевтической промышленности")
        pharma_layout = QFormLayout(self.pharma_group)
        
        # Наименование производства
        self.factory_name_input = QLineEdit()
        pharma_layout.addRow("Наименование производства:", self.factory_name_input)
        
        # Адрес производства
        self.factory_address_input = QLineEdit()
        pharma_layout.addRow("Адрес производства:", self.factory_address_input)
        
        # ID производственной линии
        self.production_line_id_input = QLineEdit()
        pharma_layout.addRow("ID производственной линии:", self.production_line_id_input)
        
        # Код продукта
        self.product_code_input = QLineEdit()
        pharma_layout.addRow("Код продукта (SKU):", self.product_code_input)
        
        # Описание продукта
        self.product_description_input = QLineEdit()
        pharma_layout.addRow("Описание продукта:", self.product_description_input)
        
        # Номер производственного заказа
        self.po_number_input = QLineEdit()
        pharma_layout.addRow("Номер производственного заказа:", self.po_number_input)
        
        # Дата начала производства
        self.expected_start_date_input = QDateEdit()
        self.expected_start_date_input.setCalendarPopup(True)
        self.expected_start_date_input.setDate(QDate.currentDate())
        pharma_layout.addRow("Дата начала производства:", self.expected_start_date_input)
        
        # Страна производства
        self.country_combo = QComboBox()
        for country in self.countries:
            self.country_combo.addItem(country.name, country.code)
        
        # Установка Беларуси по умолчанию для страны производства
        default_country_idx = self.country_combo.findData("BY")
        if default_country_idx >= 0:
            self.country_combo.setCurrentIndex(default_country_idx)
        
        pharma_layout.addRow("Страна производства:", self.country_combo)
        
        layout.addWidget(self.pharma_group)
        
        # Обязательные поля
        required_note = QLabel("* - обязательные поля")
        layout.addWidget(required_note)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Обновляем отображение в зависимости от выбранного расширения
        self.update_ui_for_extension()
    
    def on_extension_changed(self, index):
        """Обработчик изменения выбранного расширения API"""
        self.current_extension_code = self.extension_combo.itemData(index)
        self.update_ui_for_extension()
    
    def update_ui_for_extension(self):
        """Обновление интерфейса в зависимости от выбранного расширения"""
        # Показываем/скрываем блок полей для фармацевтической промышленности
        self.pharma_group.setVisible(self.current_extension_code == "pharma")
        
        # Обновляем список способов выпуска товаров в зависимости от выбранной товарной группы
        self.release_method_combo.clear()
        
        # Фильтруем типы эмиссии по выбранной товарной группе
        filtered_emission_types = []
        for emission_type in self.emission_types:
            # Если product_group равен None или совпадает с текущим расширением
            if emission_type.product_group is None or emission_type.product_group == self.current_extension_code:
                filtered_emission_types.append(emission_type)
        
        # Заполняем комбо-бокс отфильтрованными типами эмиссии
        for emission_type in filtered_emission_types:
            self.release_method_combo.addItem(emission_type.name, emission_type.code)
            
        # Добавляем дефолтные типы, если список пуст
        if self.release_method_combo.count() == 0:
            default_emission_types = [
                ("Производство", "PRODUCTION"),
                ("Импорт", "IMPORT"),
                ("Остатки", "REMAINS")
            ]
            for name, code in default_emission_types:
                self.release_method_combo.addItem(name, code)
                
        # Пытаемся установить автоматическое значение GLN для factoryId
        self.set_gln_as_factory_id()
    
    def set_gln_as_factory_id(self):
        """Устанавливает значение GLN из учетных данных в поле factoryId"""
        try:
            # Пытаемся получить родительское окно (MainWindow)
            main_window = self.parent()
            if not main_window:
                return
                
            # Если есть таблица учетных данных и в ней есть строки
            if hasattr(main_window, 'credentials_table') and main_window.credentials_table.rowCount() > 0:
                # Ищем активные учетные данные (по первой строке)
                gln_item = None
                
                # Проверяем все строки, ищем непустой GLN
                for row in range(main_window.credentials_table.rowCount()):
                    item = main_window.credentials_table.item(row, 3)  # GLN в четвертом столбце (индекс 3)
                    if item and item.text().strip():
                        gln_item = item
                        break
                        
                if gln_item and gln_item.text().strip():
                    self.factory_id_input.setText(gln_item.text().strip())
        except Exception as e:
            # Просто логируем ошибку, но не прерываем работу
            print(f"Ошибка при попытке установить GLN в factoryId: {str(e)}")
    
    def on_serial_type_changed(self, index):
        """Обработчик изменения типа серийного номера"""
        is_self_made = self.serial_type_combo.itemData(index) == "SELF_MADE"
        self.serial_numbers_input.setVisible(is_self_made)
    
    def validate_and_accept(self):
        """Проверка данных перед принятием"""
        # Извлекаем GTIN из комбобокса
        gtin_text = self.gtin_combo.currentText()
        # Если выбран элемент из списка, извлекаем GTIN из данных
        if self.gtin_combo.currentIndex() >= 0:
            gtin = self.gtin_combo.currentData()
        else:
            # Пытаемся извлечь GTIN из введенного текста
            gtin_match = re.search(r'\(([0-9]{14})\)', gtin_text)
            if gtin_match:
                gtin = gtin_match.group(1)
            else:
                gtin = gtin_text
        
        # Проверяем GTIN
        if not gtin or not re.match(r'^[0-9]{14}$', gtin):
            QMessageBox.warning(self, "Ошибка валидации", "GTIN должен состоять из 14 цифр")
            return
        
        # Проверяем обязательные поля для всех типов заказов
        if not self.factory_id_input.text():
            QMessageBox.warning(self, "Ошибка валидации", "Укажите ID производства (factoryId)")
            return
        
        if not self.factory_country_combo.currentData():
            QMessageBox.warning(self, "Ошибка валидации", "Укажите страну производителя")
            return
        
        if not self.release_method_combo.currentData():
            QMessageBox.warning(self, "Ошибка валидации", "Укажите способ выпуска товаров")
            return
        
        # Проверяем дополнительные поля для фармацевтики
        if self.current_extension_code == "pharma":
            # Здесь можно добавить дополнительные проверки для фармацевтики
            pass
        
        # Проверяем серийные номера для типа SELF_MADE
        serial_type = self.serial_type_combo.currentData()
        if serial_type == "SELF_MADE":
            serial_numbers_text = self.serial_numbers_input.toPlainText().strip()
            if not serial_numbers_text:
                QMessageBox.warning(self, "Ошибка валидации", 
                    "Для типа серийного номера SELF_MADE необходимо указать серийные номера")
                return
        
        self.accept()
    
    def get_data(self):
        """Получение данных заказа из формы"""
        # Формируем базовые данные продукта
        gtin_text = self.gtin_combo.currentText()
        if self.gtin_combo.currentIndex() >= 0:
            gtin = self.gtin_combo.currentData()
        else:
            gtin_match = re.search(r'\(([0-9]{14})\)', gtin_text)
            if gtin_match:
                gtin = gtin_match.group(1)
            else:
                gtin = gtin_text
        
        product = {
            "gtin": gtin,
            "quantity": self.quantity_input.value(),
            "serialNumberType": self.serial_type_combo.currentData(),
            "templateId": self.template_id_input.value()
        }
        
        # Если тип серийного номера SELF_MADE, добавляем серийные номера
        if product["serialNumberType"] == "SELF_MADE":
            serial_numbers_text = self.serial_numbers_input.toPlainText().strip()
            product["serialNumbers"] = [line.strip() for line in serial_numbers_text.split('\n') if line.strip()]
        
        # Формируем основной словарь заказа
        order_data = {
            "products": [product],
            # Добавляем factoryId как обязательное поле для всех типов заказов
            "factoryId": self.factory_id_input.text(),
            # Добавляем тип метода выпуска для всех типов заказов 
            "releaseMethodType": self.release_method_combo.currentData(),
            # Добавляем страну для всех типов заказов
            "factoryCountry": self.factory_country_combo.currentData()
        }
        
        # Добавляем специфичные для фармацевтики поля
        if self.current_extension_code == "pharma":
            pharma_fields = {
                "factoryName": self.factory_name_input.text(),
                "factoryAddress": self.factory_address_input.text(),
                "productionLineId": self.production_line_id_input.text(),
                "productCode": self.product_code_input.text(),
                "productDescription": self.product_description_input.text(),
                "poNumber": self.po_number_input.text(),
                "expectedStartDate": self.expected_start_date_input.date().toString("yyyy-MM-dd"),
                "country": self.country_combo.currentData()
            }
            
            # Обновляем словарь данных
            order_data.update(pharma_fields)
        
        return order_data 