from PyQt6.QtCore import QObject, pyqtSignal
import logging
import requests
from models.models import Order, Connection, Credentials, Nomenclature, Extension
import datetime
import os

logger = logging.getLogger(__name__)

class MainController(QObject):
    """Контроллер приложения"""
    def __init__(self, view, db, api_client):
        super().__init__()
        self.view = view
        self.db = db
        self.api_client = api_client
        
        # Подключение сигналов и слотов
        self.connect_signals()
        
        # Загрузка данных при запуске
        self.load_orders()
        self.load_connections()
        self.load_credentials()
        self.load_nomenclature()
        self.load_extensions()
        self.load_api_logs()
        self.load_countries()
        
        # Инициализация API-клиента с активными параметрами
        self.update_api_client_settings()
        
        # Загрузка описаний API из файла или экспорт текущих описаний
        self.load_or_export_api_descriptions()
        
        # Обновляем информацию о сервере в строке состояния
        self.update_server_status_bar()
        
        # Проверка доступности API при запуске
        self.check_api()
    
    def load_or_export_api_descriptions(self):
        """Загрузка описаний API из файла или экспорт текущих описаний"""
        api_descriptions_file = "api_descriptions.json"
        try:
            # Если файл существует, пытаемся загрузить описания
            if os.path.exists(api_descriptions_file):
                logger.info(f"Загрузка описаний методов API из файла {api_descriptions_file}")
                if self.api_client.import_descriptions_from_file(api_descriptions_file):
                    logger.info("Описания методов API успешно загружены")
                else:
                    logger.warning("Не удалось загрузить описания методов API из файла")
            else:
                # Если файл не существует, экспортируем текущие описания
                logger.info(f"Экспорт описаний методов API в файл {api_descriptions_file}")
                if self.api_client.export_descriptions_to_file(api_descriptions_file):
                    logger.info("Описания методов API успешно экспортированы")
                else:
                    logger.warning("Не удалось экспортировать описания методов API в файл")
        except Exception as e:
            logger.error(f"Ошибка при работе с описаниями методов API: {str(e)}")
    
    def connect_signals(self):
        """Подключение сигналов и слотов"""
        # Сигналы вкладки заказов
        self.view.add_order_signal.connect(self.add_order)
        self.view.ping_signal.connect(self.check_api)
        self.view.get_orders_signal.connect(self.get_orders)
        self.view.get_report_signal.connect(self.get_report)
        self.view.get_version_signal.connect(self.get_version)
        self.view.get_orders_status_signal.connect(self.get_orders_status)
        self.view.create_emission_order_signal.connect(self.create_emission_order)
        
        # Сигналы вкладки подключений
        self.view.add_connection_signal.connect(self.add_connection)
        self.view.edit_connection_signal.connect(self.edit_connection)
        self.view.delete_connection_signal.connect(self.delete_connection)
        self.view.set_active_connection_signal.connect(self.set_active_connection)
        
        # Сигналы вкладки учетных данных
        self.view.add_credentials_signal.connect(self.add_credentials)
        self.view.edit_credentials_signal.connect(self.edit_credentials)
        self.view.delete_credentials_signal.connect(self.delete_credentials)
        
        # Сигналы вкладки номенклатуры
        self.view.add_nomenclature_signal.connect(self.add_nomenclature)
        self.view.edit_nomenclature_signal.connect(self.edit_nomenclature)
        self.view.delete_nomenclature_signal.connect(self.delete_nomenclature)
        
        # Сигналы вкладки расширений API
        self.view.set_active_extension_signal.connect(self.set_active_extension)
        
        # Сигналы вкладки логов API
        self.view.load_api_logs_signal.connect(self.load_api_logs)
        self.view.get_api_log_details_signal.connect(self.on_get_api_log_details)
        self.view.export_api_descriptions_signal.connect(self.export_api_descriptions)
        
        # Сигналы вкладки стран
        self.view.load_countries_signal.connect(self.load_countries)
    
    def load_all_data(self):
        """Загрузка всех данных из базы данных"""
        self.load_orders()
        self.load_connections()
        self.load_credentials()
        self.load_nomenclature()
        self.load_extensions()
        self.load_api_logs()
    
    def load_orders(self):
        """Загрузка заказов из базы данных"""
        try:
            orders = self.db.get_orders()
            self.view.update_orders_table(orders)
            logger.info("Таблица заказов обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке заказов из базы данных: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке заказов из базы данных: {str(e)}")
    
    def load_connections(self):
        """Загрузка подключений из базы данных"""
        try:
            connections = self.db.get_connections()
            self.view.update_connections_table(connections)
            logger.info("Таблица подключений обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке подключений из базы данных: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке подключений из базы данных: {str(e)}")
    
    def load_credentials(self):
        """Загрузка учетных данных из базы данных"""
        try:
            credentials = self.db.get_credentials()
            self.view.update_credentials_table(credentials)
            logger.info("Таблица учетных данных обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке учетных данных из базы данных: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке учетных данных из базы данных: {str(e)}")
    
    def load_nomenclature(self):
        """Загрузка номенклатуры из базы данных"""
        try:
            nomenclature = self.db.get_nomenclature()
            self.view.update_nomenclature_table(nomenclature)
            logger.info("Таблица номенклатуры обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке номенклатуры из базы данных: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке номенклатуры из базы данных: {str(e)}")
    
    def load_extensions(self):
        """Загрузка расширений API из базы данных"""
        try:
            extensions = self.db.get_extensions()
            self.view.update_extensions_table(extensions)
            logger.info("Таблица расширений API обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке расширений API из базы данных: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке расширений API из базы данных: {str(e)}")
    
    def load_api_logs(self):
        """Загрузка логов API"""
        try:
            logs = self.db.get_api_logs()
            self.view.update_api_logs_table(logs)
        except Exception as e:
            logger.error(f"Ошибка при загрузке логов API: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке логов API: {str(e)}")
    
    def get_api_log_details(self, log_id):
        """Получение деталей лога API по ID"""
        try:
            log = self.db.get_api_log_by_id(log_id)
            return log
        except Exception as e:
            logger.error(f"Ошибка при получении деталей лога API: {str(e)}")
            return None
    
    def add_order(self, order_number, status):
        """Добавление нового заказа"""
        try:
            # Сохранение в базу данных
            order = self.db.add_order(order_number, status)
            logger.info(f"Заказ {order_number} сохранен в базе данных")
            
            try:
                # Отправка на сервер
                response = self.api_client.post_orders({
                    "order_number": order_number,
                    "status": status
                })
                logger.info(f"Заказ {order_number} отправлен на сервер")
            except requests.RequestException as e:
                logger.warning(f"Не удалось отправить заказ на сервер: {str(e)}")
                self.view.show_message("Предупреждение", 
                    "Заказ сохранен локально, но не отправлен на сервер из-за ошибки подключения")
                
            # Обновление интерфейса
            self.load_orders()
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении заказа: {str(e)}")
    
    def update_api_client_settings(self):
        """Обновление настроек API-клиента из базы данных"""
        # Получаем активное подключение
        connection = self.db.get_active_connection()
        if connection:
            self.api_client.base_url = connection.url
            # Обновляем информацию о сервере в строке состояния
            self.view.update_server_status(connection.name, connection.url)
            
            # Получаем учетные данные для активного подключения
            credentials_list = self.db.get_credentials_for_connection(connection.id)
            if credentials_list:
                # Используем первые учетные данные для этого подключения
                self.api_client.omsid = credentials_list[0].omsid
                # Токен будет использоваться в запросе ping
        else:
            # Если нет активного подключения, очищаем информацию в строке состояния
            self.view.update_server_status("", "")
        
        # Получаем активное расширение API
        extension = self.db.get_active_extension()
        if extension:
            self.api_client.extension = extension.code
        
        # Если OMSID еще не установлен, получаем из настроек или первых учетных данных
        if not hasattr(self.api_client, 'omsid') or not self.api_client.omsid:
            omsid = self.db.get_setting("omsid", "")
            if not omsid:
                # Здесь мы берем любые учетные данные, не важно к какому подключению они привязаны
                credentials = self.db.get_credentials()
                if credentials:
                    omsid = credentials[0].omsid
                    # Сохраняем в настройки для будущего использования
                    self.db.set_setting("omsid", omsid)
            self.api_client.omsid = omsid
        
        # Устанавливаем ссылку на базу данных в API-клиенте для логирования
        self.api_client.db = self.db

    def check_api(self):
        """Проверка доступности API"""
        try:
            # Обновляем настройки API-клиента перед проверкой
            self.update_api_client_settings()
            
            if not self.api_client.base_url:
                logger.warning("Нет активного подключения")
                self.view.show_message("Предупреждение", 
                    "Нет активного подключения. Настройте подключение перед проверкой API.")
                self.view.update_api_status(False)
                return
                
            if not self.api_client.omsid:
                logger.warning("Не указан OMSID")
                self.view.show_message("Предупреждение", 
                    "Не указан OMSID. Добавьте учетные данные перед проверкой API.")
                self.view.update_api_status(False)
                return
                
            response = self.api_client.get_ping()
            logger.info(f"API доступен: {response}")
            self.view.update_api_status(True)
            self.view.show_message("Проверка API", "API доступен")
            self.load_api_logs()  # Обновляем логи после проверки
        except requests.RequestException as e:
            logger.warning(f"API недоступен: {str(e)}")
            self.view.update_api_status(False)
            self.view.show_message("Предупреждение", 
                f"API недоступен: {str(e)}. Приложение работает в автономном режиме")
            self.load_api_logs()  # Обновляем логи после проверки
        except Exception as e:
            logger.error(f"Ошибка при проверке API: {str(e)}")
            self.view.update_api_status(False)
            self.view.show_message("Ошибка", f"Ошибка при проверке API: {str(e)}")
            self.load_api_logs()  # Обновляем логи после проверки
    
    def get_orders(self):
        """Получение заказов с сервера"""
        try:
            response = self.api_client.get_orders()
            # Обработка ответа и сохранение в базу данных
            for order_data in response.get("orders", []):
                self.db.add_order(
                    order_data["order_number"],
                    order_data["status"]
                )
            self.load_orders()
            logger.info("Заказы успешно загружены с сервера")
            self.view.show_message("Успех", "Заказы успешно загружены")
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить заказы с сервера: {str(e)}")
            self.view.show_message("Предупреждение", 
                "Не удалось получить заказы с сервера. Показаны локальные данные")
        except Exception as e:
            logger.error(f"Ошибка при загрузке заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке заказов: {str(e)}")
    
    def get_report(self):
        """Получение отчета"""
        try:
            response = self.api_client.get_report()
            logger.info("Отчет успешно получен")
            self.view.show_message("Отчет", str(response))
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить отчет: {str(e)}")
            self.view.show_message("Предупреждение", 
                "Не удалось получить отчет. Сервер недоступен")
        except Exception as e:
            logger.error(f"Ошибка при получении отчета: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении отчета: {str(e)}")
    
    def get_orders_status(self):
        """Получение статуса заказов"""
        try:
            # Обновляем настройки API-клиента перед отправкой запроса
            self.update_api_client_settings()
            
            # Проверяем наличие активного подключения
            if not self.api_client.base_url:
                logger.warning("Нет активного подключения")
                self.view.show_message("Предупреждение", 
                    "Нет активного подключения. Настройте подключение перед запросом статуса заказов.")
                return
            
            # Проверяем наличие omsId
            if not self.api_client.omsid:
                logger.warning("Не указан OMSID")
                self.view.show_message("Предупреждение", 
                    "Не указан OMSID. Добавьте учетные данные перед запросом статуса заказов.")
                return
            
            # Получаем статус заказов через API
            response = self.api_client.get_orders_status()
            
            # Выводим информацию и сохраняем логи
            logger.info(f"Получена информация о статусе заказов: {response}")
            
            # Формируем сообщение для пользователя
            if "orderInfos" in response and response["orderInfos"]:
                orders_count = len(response["orderInfos"])
                message = f"Получена информация о {orders_count} заказах.\n\n"
                
                for i, order_info in enumerate(response["orderInfos"][:5]):  # Показываем первые 5 заказов
                    message += f"Заказ #{i+1}:\n"
                    message += f"ID: {order_info.get('orderId', 'Не указан')}\n"
                    message += f"Статус: {order_info.get('orderStatus', 'Неизвестен')}\n"
                    message += f"Создан: {datetime.datetime.fromtimestamp(order_info.get('createdTimestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    if "declineReason" in order_info and order_info["declineReason"]:
                        message += f"Причина отклонения: {order_info['declineReason']}\n"
                    
                    message += "\n"
                
                if orders_count > 5:
                    message += f"... и еще {orders_count - 5} заказов."
            else:
                message = "Заказы не найдены или ответ сервера не содержит информации о заказах."
            
            # Отображаем результат
            self.view.show_message("Статус заказов", message)
            
            # Обновляем логи
            self.load_api_logs()
            
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить статус заказов: {str(e)}")
            self.view.show_message("Предупреждение", 
                f"Не удалось получить статус заказов. Сервер недоступен: {str(e)}")
            self.load_api_logs()  # Обновляем логи после ошибки
        except Exception as e:
            logger.error(f"Ошибка при получении статуса заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении статуса заказов: {str(e)}")
            self.load_api_logs()  # Обновляем логи после ошибки
    
    def get_version(self):
        """Получение версии СУЗ и API"""
        try:
            # Обновляем настройки API-клиента перед отправкой запроса
            self.update_api_client_settings()
            
            # Проверяем наличие активного подключения
            if not self.api_client.base_url:
                logger.warning("Нет активного подключения")
                self.view.show_message("Предупреждение", 
                    "Нет активного подключения. Настройте подключение перед запросом версии.")
                return
            
            # Получаем версию через API
            response = self.api_client.get_version()
            
            # Формируем сообщение с информацией о версии
            version_message = (
                f"Версия API СУЗ: {response.get('apiVersion', 'Не указана')}\n"
                f"Версия СУЗ: {response.get('omsVersion', 'Не указана')}"
            )
            
            logger.info(f"Получена информация о версии: {response}")
            self.view.show_message("Информация о версии", version_message)
            
            # Обновляем логи
            self.load_api_logs()
            
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить информацию о версии: {str(e)}")
            self.view.show_message("Предупреждение", 
                f"Не удалось получить информацию о версии. Сервер недоступен: {str(e)}")
            self.load_api_logs()  # Обновляем логи после ошибки
        except Exception as e:
            logger.error(f"Ошибка при получении информации о версии: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении информации о версии: {str(e)}")
            self.load_api_logs()  # Обновляем логи после ошибки
    
    # Методы для работы с подключениями
    def add_connection(self, name, url):
        """Добавление нового подключения"""
        try:
            connection = self.db.add_connection(name, url)
            logger.info(f"Подключение {name} добавлено")
            self.load_connections()
            self.view.show_message("Успех", "Подключение успешно добавлено")
        except Exception as e:
            logger.error(f"Ошибка при добавлении подключения: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении подключения: {str(e)}")
    
    def edit_connection(self, connection_id, name, url):
        """Редактирование подключения"""
        try:
            connection = self.db.update_connection(connection_id, name, url)
            logger.info(f"Подключение {name} обновлено")
            self.load_connections()
            self.view.show_message("Успех", "Подключение успешно обновлено")
        except Exception as e:
            logger.error(f"Ошибка при обновлении подключения: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при обновлении подключения: {str(e)}")
    
    def delete_connection(self, connection_id):
        """Удаление подключения"""
        try:
            self.db.delete_connection(connection_id)
            logger.info(f"Подключение {connection_id} удалено")
            self.load_connections()
            self.load_credentials()  # Обновляем учетные данные, так как они связаны с подключениями
            self.view.show_message("Успех", "Подключение успешно удалено")
        except Exception as e:
            logger.error(f"Ошибка при удалении подключения: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении подключения: {str(e)}")
    
    def set_active_connection(self, connection_id):
        """Установка активного подключения"""
        try:
            self.db.set_active_connection(connection_id)
            connection = self.db.get_connection_by_id(connection_id)
            if connection:
                self.api_client.base_url = connection.url
                logger.info(f"Активное подключение изменено на {connection.name}")
                # Обновляем интерфейс
                self.load_connections()  # Обновляем таблицу подключений
                self.view.update_server_status(connection.name, connection.url)  # Обновляем строку состояния
                self.view.show_message("Успех", f"Активное подключение изменено на {connection.name}")
        except Exception as e:
            logger.error(f"Ошибка при установке активного подключения: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при установке активного подключения: {str(e)}")
    
    # Методы для работы с учетными данными
    def add_credentials(self, omsid, token, connection_id):
        """Добавление новых учетных данных"""
        try:
            credentials = self.db.add_credentials(omsid, token, connection_id)
            logger.info(f"Учетные данные для подключения {connection_id} добавлены")
            self.load_credentials()
            self.view.show_message("Успех", "Учетные данные успешно добавлены")
        except Exception as e:
            logger.error(f"Ошибка при добавлении учетных данных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении учетных данных: {str(e)}")
    
    def edit_credentials(self, credentials_id, omsid, token):
        """Редактирование учетных данных"""
        try:
            credentials = self.db.update_credentials(credentials_id, omsid, token)
            logger.info(f"Учетные данные {credentials_id} обновлены")
            self.load_credentials()
            self.view.show_message("Успех", "Учетные данные успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении учетных данных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при обновлении учетных данных: {str(e)}")
    
    def delete_credentials(self, credentials_id):
        """Удаление учетных данных"""
        try:
            self.db.delete_credentials(credentials_id)
            logger.info(f"Учетные данные {credentials_id} удалены")
            self.load_credentials()
            self.view.show_message("Успех", "Учетные данные успешно удалены")
        except Exception as e:
            logger.error(f"Ошибка при удалении учетных данных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении учетных данных: {str(e)}")
    
    # Методы для работы с номенклатурой
    def add_nomenclature(self, name, gtin, product_group=""):
        """Добавление новой номенклатуры"""
        try:
            nomenclature = self.db.add_nomenclature(name, gtin, product_group)
            logger.info(f"Номенклатура {name} добавлена")
            self.load_nomenclature()
            self.view.show_message("Успех", "Номенклатура успешно добавлена")
        except Exception as e:
            logger.error(f"Ошибка при добавлении номенклатуры: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении номенклатуры: {str(e)}")
    
    def edit_nomenclature(self, nomenclature_id, name, gtin, product_group=""):
        """Редактирование номенклатуры"""
        try:
            nomenclature = self.db.update_nomenclature(nomenclature_id, name, gtin, product_group)
            logger.info(f"Номенклатура {name} обновлена")
            self.load_nomenclature()
            self.view.show_message("Успех", "Номенклатура успешно обновлена")
        except Exception as e:
            logger.error(f"Ошибка при обновлении номенклатуры: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при обновлении номенклатуры: {str(e)}")
    
    def delete_nomenclature(self, nomenclature_id):
        """Удаление номенклатуры"""
        try:
            self.db.delete_nomenclature(nomenclature_id)
            logger.info(f"Номенклатура {nomenclature_id} удалена")
            self.load_nomenclature()
            self.view.show_message("Успех", "Номенклатура успешно удалена")
        except Exception as e:
            logger.error(f"Ошибка при удалении номенклатуры: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении номенклатуры: {str(e)}")
    
    # Методы для работы с расширениями API
    def set_active_extension(self, extension_id):
        """Установка активного расширения API"""
        try:
            self.db.set_active_extension(extension_id)
            extension = self.db.get_active_extension()  # Получаем активное расширение из БД
            if extension:
                self.api_client.extension = extension.code
                logger.info(f"Активное расширение API изменено на {extension.name}")
                self.load_extensions()  # Обновляем таблицу расширений
                self.view.show_message("Успех", f"Активное расширение API изменено на {extension.name}")
        except Exception as e:
            logger.error(f"Ошибка при установке активного расширения API: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при установке активного расширения API: {str(e)}")
    
    def on_get_api_log_details(self, log_id, request_callback, response_callback):
        """Обработчик запроса деталей лога API"""
        try:
            log = self.db.get_api_log_by_id(log_id)
            if log:
                # Передаем данные запроса и ответа через callback функции
                request_callback(log["request"])
                response_callback(log["response"])
            else:
                request_callback("{}")
                response_callback("{}")
                
        except Exception as e:
            logger.error(f"Ошибка при получении деталей лога API: {str(e)}")
            request_callback(f"{{ \"error\": \"{str(e)}\" }}")
            response_callback(f"{{ \"error\": \"{str(e)}\" }}")
    
    def create_emission_order(self, order_data):
        """Создание заказа на эмиссию кодов маркировки
        
        Создает и отправляет заказ на эмиссию кодов маркировки через API.
        
        Args:
            order_data (dict): Данные заказа для отправки
        """
        try:
            # Обновляем настройки API-клиента перед отправкой запроса
            self.update_api_client_settings()
            
            # Проверяем наличие активного подключения
            if not self.api_client.base_url:
                logger.warning("Нет активного подключения")
                self.view.show_message("Предупреждение", 
                    "Нет активного подключения. Настройте подключение перед созданием заказа.")
                return
            
            # Проверяем наличие omsId
            if not self.api_client.omsid:
                logger.warning("Не указан OMSID")
                self.view.show_message("Предупреждение", 
                    "Не указан OMSID. Добавьте учетные данные перед созданием заказа.")
                return
            
            # Получаем активное расширение
            extension = self.db.get_active_extension()
            if not extension:
                self.view.show_message("Предупреждение", 
                    "Не выбрано активное расширение API. Выберите расширение перед созданием заказа.")
                return
            
            # Если выбрана фармацевтика, проверяем обязательные поля
            if extension.code == "pharma":
                # Базовые проверки уже реализованы в методе create_order класса APIClient
                pass
            
            # Отправляем запрос на создание заказа
            response = self.api_client.create_order(order_data)
            
            # Формируем и выводим сообщение с результатом
            if "orderId" in response:
                message = f"Заказ на эмиссию кодов успешно создан\n\nID заказа: {response['orderId']}"
                logger.info(f"Создан заказ на эмиссию кодов, ID: {response['orderId']}")
                self.view.show_message("Успех", message)
            else:
                error_message = response.get("error", {}).get("message", "Неизвестная ошибка")
                logger.warning(f"Ошибка при создании заказа: {error_message}")
                self.view.show_message("Ошибка", f"Не удалось создать заказ: {error_message}")
            
            # Обновляем логи API
            self.load_api_logs()
            
        except ValueError as e:
            # Обрабатываем ошибки валидации
            logger.warning(f"Ошибка валидации данных заказа: {str(e)}")
            self.view.show_message("Ошибка валидации", str(e))
        except requests.RequestException as e:
            # Обрабатываем ошибки соединения
            logger.warning(f"Ошибка соединения при создании заказа: {str(e)}")
            self.view.show_message("Ошибка соединения", 
                f"Не удалось создать заказ. Сервер недоступен: {str(e)}")
            self.load_api_logs()
        except Exception as e:
            # Обрабатываем прочие ошибки
            logger.error(f"Непредвиденная ошибка при создании заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Непредвиденная ошибка при создании заказа: {str(e)}")
            self.load_api_logs() 
    
    def load_countries(self):
        """Загрузка списка стран из базы данных"""
        try:
            countries = self.db.get_countries()
            self.view.update_countries_table(countries)
            logger.info(f"Загружено {len(countries)} стран")
        except Exception as e:
            logger.error(f"Ошибка при загрузке стран: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось загрузить список стран: {str(e)}")

    def export_api_descriptions(self):
        """Экспорт описаний API в файл"""
        try:
            api_descriptions_file = "api_descriptions.json"
            logger.info(f"Экспорт описаний методов API в файл {api_descriptions_file}")
            if self.api_client.export_descriptions_to_file(api_descriptions_file):
                logger.info("Описания методов API успешно экспортированы")
                self.view.show_message("Успех", "Описания методов API успешно экспортированы")
            else:
                logger.warning("Не удалось экспортировать описания методов API в файл")
                self.view.show_message("Предупреждение", "Не удалось экспортировать описания методов API в файл")
        except Exception as e:
            logger.error(f"Ошибка при экспорте описаний API: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при экспорте описаний API: {str(e)}")

    def update_server_status_bar(self):
        """Обновление информации о сервере в строке состояния"""
        connection = self.db.get_active_connection()
        if connection:
            self.view.update_server_status(connection.name, connection.url)
        else:
            self.view.update_server_status("", "") 