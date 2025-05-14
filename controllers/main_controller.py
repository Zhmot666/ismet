from PyQt6.QtCore import QObject, pyqtSignal
import logging
import requests
from models.models import Order, Connection, Credentials, Nomenclature, Extension, EmissionType, Country, OrderStatus, APIOrder
import datetime
import os
import time
import json
from typing import List, Dict, Union, Optional, Any, Callable
from PyQt6.QtCore import Qt

from models.database import Database
from models.api_client import APIClient
from models.api_log import APILog

logger = logging.getLogger(__name__)

class MainController(QObject):
    """Контроллер приложения"""
    def __init__(self, view, db, api_client, api_logger):
        super().__init__()
        self.view = view
        self.db = db
        self.api_client = api_client
        self.api_logger = api_logger
        
        # Устанавливаем ссылку на базу данных в объект view
        self.view.db = self.db
        
        # Подключение сигналов и слотов
        self.connect_signals()
        
        # Загрузка данных при запуске
        self.load_orders()
        self.load_api_orders_from_db()  # Загружаем API заказы из базы данных
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
        
        # Загрузка кодов маркировки при инициализации данных
        self.load_marking_codes()
    
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
        """Подключение сигналов к слотам"""
        # Сигналы от view к controller
        
        # API заказы
        self.view.api_orders_signal.connect(self.load_api_orders)
        self.view.delete_api_order_signal.connect(self.delete_api_order)
        self.view.get_km_from_order_signal.connect(self.get_km_from_order)
        
        # Сигналы для работы с заказами
        self.view.get_orders_signal.connect(self.get_orders)
        self.view.get_order_details_signal.connect(self.get_order_details)
        self.view.add_order_signal.connect(self.add_order)
        self.view.ping_signal.connect(self.check_api)
        self.view.get_orders_status_signal.connect(self.get_orders_status)
        self.view.get_report_signal.connect(self.get_report)
        self.view.get_version_signal.connect(self.get_version)
        self.view.create_emission_order_signal.connect(self.create_emission_order)
        
        # Сигналы для работы с подключениями
        self.view.add_connection_signal.connect(self.add_connection)
        self.view.edit_connection_signal.connect(self.edit_connection)
        self.view.delete_connection_signal.connect(self.delete_connection)
        self.view.set_active_connection_signal.connect(self.set_active_connection)
        
        # Сигналы для работы с учетными данными
        self.view.add_credentials_signal.connect(self.add_credentials)
        self.view.edit_credentials_signal.connect(self.edit_credentials)
        self.view.delete_credentials_signal.connect(self.delete_credentials)
        
        # Сигналы для работы с номенклатурой
        self.view.add_nomenclature_signal.connect(self.add_nomenclature)
        self.view.edit_nomenclature_signal.connect(self.edit_nomenclature)
        self.view.delete_nomenclature_signal.connect(self.delete_nomenclature)
        
        # Сигналы для работы с расширениями API
        self.view.set_active_extension_signal.connect(self.set_active_extension)
        
        # Сигналы для работы с логами API
        self.view.load_api_logs_signal.connect(self.load_api_logs)
        self.view.get_api_log_details_signal.connect(self.on_get_api_log_details)
        self.view.export_api_descriptions_signal.connect(self.export_api_descriptions)
        
        # Сигналы для работы со странами
        self.view.load_countries_signal.connect(self.load_countries)
        
        # Сигналы для работы со статусами заказов
        self.view.load_order_statuses_signal.connect(self.load_order_statuses)
        self.view.add_order_status_signal.connect(self.add_order_status)
        self.view.edit_order_status_signal.connect(self.edit_order_status)
        self.view.delete_order_status_signal.connect(self.delete_order_status)
        
        # Сигналы для работы с типами использования кодов маркировки
        self.view.load_usage_types_signal.connect(self.load_usage_types)
        self.view.add_usage_type_signal.connect(self.add_usage_type)
        self.view.edit_usage_type_signal.connect(self.update_usage_type)
        self.view.delete_usage_type_signal.connect(self.delete_usage_type)
        
        # Сигналы для работы с кодами маркировки
        self.view.get_marking_codes_signal.connect(self.get_marking_codes)
        self.view.mark_codes_as_used_signal.connect(self.mark_codes_as_used)
        self.view.mark_codes_as_exported_signal.connect(self.mark_codes_as_exported)
        
        # Сигналы для работы с файлами агрегации
        self.view.load_aggregation_files_signal.connect(self.load_aggregation_files)
        self.view.add_aggregation_file_signal.connect(self.add_aggregation_file)
        self.view.delete_aggregation_file_signal.connect(self.delete_aggregation_file)
        self.view.export_aggregation_file_signal.connect(self.export_aggregation_file)
        self.view.send_utilisation_report_signal.connect(self.send_utilisation_report)
    
    def load_all_data(self):
        """Загрузка всех данных из базы данных"""
        self.load_connections()
        self.load_credentials()
        self.load_nomenclature()
        self.load_extensions()
        self.load_orders()
        self.load_countries()
        self.load_order_statuses()
        self.load_api_logs()
        self.load_marking_codes()
        self.load_aggregation_files()
    
    def load_orders(self):
        """Загрузка заказов из базы данных"""
        try:
            orders = self.db.get_orders()
            self.view.update_orders_table(orders)
            logger.info("Таблица заказов обновлена")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении списка заказов: {str(e)}")
    
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
            order = self.db.add_order(order_number=order_number, status=status)
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
        try:
            # Получаем активное подключение
            connection = self.db.get_active_connection()
            if connection:
                self.api_client.base_url = connection.url
                # Обновляем информацию о сервере в строке состояния
                self.view.update_server_status(connection.name, connection.url)
                
                # Получаем учетные данные для активного подключения
                try:
                    credentials_list = self.db.get_credentials_for_connection(connection.id)
                    if credentials_list:
                        # Используем первые учетные данные для этого подключения
                        self.api_client.omsid = credentials_list[0].omsid
                        # Токен будет использоваться в запросе ping
                except Exception as e:
                    logger.warning(f"Не удалось получить учетные данные для подключения: {str(e)}")
            else:
                # Если нет активного подключения, очищаем информацию в строке состояния
                self.view.update_server_status("", "")
            
            # Получаем активное расширение API
            try:
                extension = self.db.get_active_extension()
                if extension:
                    self.api_client.extension = extension.code
            except Exception as e:
                logger.warning(f"Не удалось получить активное расширение API: {str(e)}")
            
            # Если OMSID еще не установлен, получаем из настроек или первых учетных данных
            if not hasattr(self.api_client, 'omsid') or not self.api_client.omsid:
                try:
                    omsid = self.db.get_setting("omsid", "")
                    if not omsid:
                        # Здесь мы берем любые учетные данные, не важно к какому подключению они привязаны
                        credentials = self.db.get_credentials()
                        if credentials:
                            omsid = credentials[0].omsid
                            # Сохраняем в настройки для будущего использования
                            self.db.set_setting("omsid", omsid)
                    self.api_client.omsid = omsid
                except Exception as e:
                    logger.warning(f"Не удалось получить OMSID: {str(e)}")
                    self.api_client.omsid = ""
            
            # Устанавливаем ссылку на базу данных в API-клиенте для логирования
            self.api_client.db = self.db
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек API-клиента: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при обновлении настроек API-клиента: {str(e)}")

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
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
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
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
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
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить отчет: {str(e)}")
            self.view.show_message("Предупреждение", "Не удалось получить отчет")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except Exception as e:
            logger.error(f"Ошибка при получении отчета: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении отчета: {str(e)}")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
    
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
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить статус заказов: {str(e)}")
            self.view.show_message("Предупреждение", 
                f"Не удалось получить статус заказов. Сервер недоступен: {str(e)}")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении статуса заказов: {str(e)}")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
    
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
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except requests.RequestException as e:
            logger.warning(f"Не удалось получить информацию о версии: {str(e)}")
            self.view.show_message("Предупреждение", 
                f"Не удалось получить информацию о версии. Сервер недоступен: {str(e)}")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о версии: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении информации о версии: {str(e)}")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
    
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
    def add_credentials(self, omsid, token, gln, connection_id):
        """Добавление новых учетных данных"""
        try:
            # Сохранение в базу данных
            self.db.add_credentials(omsid=omsid, token=token, gln=gln, connection_id=connection_id)
            logger.info(f"Учетные данные для {omsid} сохранены в базе данных")
            
            # Обновление интерфейса
            self.load_credentials()
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении учетных данных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении учетных данных: {str(e)}")
    
    def edit_credentials(self, credentials_id, omsid, token, gln):
        """Редактирование учетных данных"""
        try:
            credentials = self.db.update_credentials(credentials_id, omsid, token, gln)
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
        # Подготавливаем переменные для сохранения данных заказа
        from datetime import datetime
        import time
        
        order_id = "Не указан"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expected_complete_ms = 0
        expected_complete_min = 0
        expected_complete_str = ""
        status = "Непринят"  # По умолчанию статус "Непринят"
        response = None
        
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
            
            # Создаем заказ через API
            response = self.api_client.create_order(order_data)
            
            # Обновляем данные для сохранения заказа
            if response:
                order_id = response.get("orderId", "Не указан")
                expected_complete_ms = response.get("expectedCompleteTimestamp", 0)
                
                # Преобразуем миллисекунды в дату и время
                expected_complete = None
                if expected_complete_ms:
                    # Конвертируем миллисекунды в дату/время, проверяя размер значения
                    # Если значение слишком маленькое (меньше 13 знаков), это секунды
                    timestamp_value = expected_complete_ms
                    # Проверяем, если значение маленькое (менее 10000000000), это может быть в секундах или минутах
                    if timestamp_value < 10000000000:
                        # Предполагаем, что это минуты, конвертируем в миллисекунды
                        timestamp_value = timestamp_value * 60 * 1000
                    
                    # Теперь преобразуем в дату
                    expected_complete = datetime.fromtimestamp(timestamp_value / 1000)
                    expected_complete_str = expected_complete.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Добавим сообщение в лог для отладки
                    logger.info(f"Преобразование времени ожидания: {expected_complete_ms} мс -> {expected_complete_str}")
                else:
                    expected_complete_str = ""
                
                # Определяем статус заказа
                # Проверяем несколько полей для определения успешности
                if response.get("success", False) or response.get("orderId") or response.get("orderInfos"):
                    status = "Принят" 
                    logger.info(f"Заказ на эмиссию успешно создан. Идентификатор заказа: {order_id}")
                    self.view.show_message("Успех", f"Заказ на эмиссию успешно создан. ID заказа: {order_id}")
                else:
                    status = "Непринят"
                    error_message = "Ошибка при создании заказа"
                    if "globalErrors" in response:
                        error_message += ": " + ", ".join(response["globalErrors"])
                    elif "error" in response:
                        error_message += ": " + str(response["error"])
                
                    logger.warning(error_message)
                    self.view.show_message("Предупреждение", error_message)
            
            # Убираем дублирующийся код проверки success
            else:
                # Если response пустой, сохраняем информацию об ошибке
                logger.warning("Пустой ответ от сервера при создании заказа")
                self.view.show_message("Предупреждение", "Ошибка при создании заказа: пустой ответ от сервера")
        
        except ValueError as e:
            logger.error(f"Ошибка валидации данных заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка валидации данных заказа: {str(e)}")
            return
        except requests.RequestException as e:
            logger.error(f"Ошибка сети при создании заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка сети при создании заказа: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при создании заказа: {str(e)}")
        
        # Сохраняем заказ в базу данных независимо от успешности отправки запроса
        try:
            # Сохраняем основную информацию о заказе
            saved_order = self.db.add_order(
                order_number=str(order_id),
                timestamp=timestamp,
                expected_complete=expected_complete_str,
                status=status
            )
            
            # Сохраняем детали заказа (товары)
            for product in order_data.get("products", []):
                self.db.add_order_product(
                    order_id=saved_order.id,
                    gtin=product.get("gtin", ""),
                    quantity=product.get("quantity", 0)
                )
            
            # Обновляем таблицу заказов
            self.load_orders()
            logger.info(f"Заказ сохранен в базу данных со статусом '{status}'")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении заказа в базу данных: {str(e)}")
            self.view.show_message("Ошибка", f"Заказ был отправлен, но не сохранен в базу данных: {str(e)}")
    
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

    def get_order_details(self, order_id):
        """Получение деталей заказа"""
        try:
            products = self.db.get_order_products(order_id)
            self.view.update_order_details_table(products)
            logger.info(f"Детали заказа {order_id} загружены")
        except Exception as e:
            logger.error(f"Ошибка при загрузке деталей заказа: {str(e)}")
            self.view.show_message("Ошибка", 
                f"Ошибка при загрузке деталей заказа: {str(e)}")

    def get_api_orders(self):
        """Получение заказов из API в новом формате для вкладки API заказы
        
        Внимание: Этот метод должен вызываться только по прямому запросу пользователя (кнопка "Обновить заказы"),
        так как на сервере есть ограничение по количеству вызовов API.
        """
        try:
            # Обновляем настройки API-клиента перед отправкой запроса
            self.update_api_client_settings()
            
            # Проверяем наличие активного подключения
            if not self.api_client.base_url:
                logger.warning("Нет активного подключения")
                self.view.show_message("Предупреждение", 
                    "Нет активного подключения. Настройте подключение перед запросом заказов.")
                return
            
            # Проверяем наличие omsId
            if not self.api_client.omsid:
                logger.warning("Не указан OMSID")
                self.view.show_message("Предупреждение", 
                    "Не указан OMSID. Добавьте учетные данные перед запросом заказов.")
                return
            
            # Получаем статус заказов через API
            response = self.api_client.get_orders_status()
            
            # Проверяем, есть ли информация о заказах в ответе
            if "orderInfos" in response and response["orderInfos"]:
                order_infos = response["orderInfos"]
                
                # Создаем объекты APIOrder для сохранения в базу данных
                api_orders = []
                
                for order_info in order_infos:
                    # Форматируем timestamp из миллисекунд в читаемый формат
                    timestamp_ms = order_info.get("createdTimestamp", 0)
                    if timestamp_ms:
                        try:
                            # Преобразуем миллисекунды в дату/время
                            dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)
                            formatted_date = dt.strftime("%d.%m.%Y %H:%M:%S")
                            order_info["createdTimestamp"] = formatted_date
                        except Exception as e:
                            logger.warning(f"Не удалось преобразовать timestamp: {e}")

                    # Добавляем русские названия полей в буферы для более удобного отображения
                    buffers = order_info.get("buffers", [])
                    for buffer in buffers:
                        # Используем оригинальные данные, но добавляем русские названия
                        buffer["Заказ"] = buffer.get("orderId", "")
                        buffer["Товар"] = buffer.get("gtin", "")
                        buffer["Осталось"] = buffer.get("leftInBuffer", -1)
                        buffer["Пулы исчерпаны"] = "Да" if buffer.get("poolsExhausted", False) else "Нет"
                        buffer["Всего кодов"] = buffer.get("totalCodes", -1)
                        buffer["Недоступно"] = buffer.get("unavailableCodes", -1)
                        buffer["Доступно"] = buffer.get("availableCodes", -1)
                        buffer["Передано"] = buffer.get("totalPassed", -1)
                        buffer["OMS ID"] = buffer.get("omsId", "")

                    api_order = APIOrder(
                        order_id=order_info.get("orderId", ""),
                        order_status=order_info.get("orderStatus", ""),
                        created_timestamp=order_info.get("createdTimestamp", ""),
                        total_quantity=order_info.get("totalQuantity", 0),
                        num_of_products=order_info.get("numOfProducts", 0),
                        product_group_type=order_info.get("productGroupType", ""),
                        signed=order_info.get("signed", False),
                        verified=order_info.get("verified", False),
                        buffers=buffers
                    )
                    api_orders.append(api_order)
                
                # Сохраняем API заказы в базу данных
                self.db.save_api_orders(api_orders)
                
                # ВАЖНО: Загружаем данные заново из базы данных, чтобы отобразить
                # как обновленные заказы, так и помеченные как устаревшие
                self.load_api_orders_from_db()
                
                logger.info(f"Загружено и сохранено {len(order_infos)} API заказов")
                self.view.show_message("Успех", f"Загружено и сохранено {len(order_infos)} API заказов")
            else:
                # Если нет данных, помечаем все существующие заказы как устаревшие,
                # но не очищаем таблицу полностью
                existing_api_orders = self.db.get_api_orders()
                if existing_api_orders:
                    # Создаем пустой список заказов (что приведет к отметке всех существующих как устаревших)
                    self.db.save_api_orders([])
                    # Загружаем данные заново для отображения устаревших заказов
                    self.load_api_orders_from_db()
                    
                self.view.show_message("Информация", "Заказы не найдены в API")
            
            # Обновляем таблицу логов API
            self.load_api_logs()
        
        except Exception as e:
            logger.error(f"Ошибка при получении API заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении API заказов: {str(e)}")
            self.load_api_logs()

    # Методы для работы со статусами заказов
    def load_order_statuses(self):
        """Загрузка статусов заказов из базы данных"""
        try:
            # Загружаем статусы заказов из базы данных
            statuses = self.db.get_order_statuses()
            logger.info(f"Загружено {len(statuses)} статусов заказов")
            
            # Обновляем таблицу статусов заказов в представлении
            self.view.update_order_statuses_table(statuses)
        except Exception as e:
            logger.error(f"Ошибка при загрузке статусов заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке статусов заказов: {str(e)}")
    
    def add_order_status(self, code, name, description=""):
        """Добавление статуса заказа в базу данных"""
        try:
            # Проверяем, что код и название не пустые
            if not code or not name:
                self.view.show_message("Ошибка", "Код и название статуса не могут быть пустыми")
                return
            
            # Добавляем статус заказа в базу данных
            status = self.db.add_order_status(code, name, description)
            logger.info(f"Добавлен статус заказа: {code} - {name}")
            
            # Явно сохраняем изменения в базу данных
            self.db.commit()
            
            # Обновляем таблицу статусов заказов в представлении
            self.load_order_statuses()
            
            # Показываем сообщение об успешном добавлении
            self.view.show_message("Успех", f"Статус заказа '{name}' успешно добавлен")
        except Exception as e:
            logger.error(f"Ошибка при добавлении статуса заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при добавлении статуса заказа: {str(e)}")
    
    def edit_order_status(self, status_id, code, name, description=""):
        """Редактирование статуса заказа в базе данных"""
        try:
            # Проверяем, что код и название не пустые
            if not code or not name:
                self.view.show_message("Ошибка", "Код и название статуса не могут быть пустыми")
                return
            
            # Обновляем статус заказа в базе данных
            status = self.db.update_order_status(status_id, code, name, description)
            logger.info(f"Обновлен статус заказа: {code} - {name}")
            
            # Явно сохраняем изменения в базу данных
            self.db.commit()
            
            # Обновляем таблицу статусов заказов в представлении
            self.load_order_statuses()
            
            # Показываем сообщение об успешном обновлении
            self.view.show_message("Успех", f"Статус заказа '{name}' успешно обновлен")
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при обновлении статуса заказа: {str(e)}")
    
    def delete_order_status(self, status_id):
        """Удаление статуса заказа из базы данных"""
        try:
            # Удаляем статус заказа из базы данных
            self.db.delete_order_status(status_id)
            logger.info(f"Удален статус заказа с ID: {status_id}")
            
            # Явно сохраняем изменения в базу данных
            self.db.commit()
            
            # Обновляем таблицу статусов заказов в представлении
            self.load_order_statuses()
            
            # Показываем сообщение об успешном удалении
            self.view.show_message("Успех", "Статус заказа успешно удален")
        except Exception as e:
            logger.error(f"Ошибка при удалении статуса заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении статуса заказа: {str(e)}")

    def load_api_orders_from_db(self):
        """Загрузка сохраненных API заказов из базы данных
        
        Этот метод загружает сохраненные ранее API заказы из локальной базы данных
        без выполнения API запросов к серверу.
        """
        try:
            # Получаем сохраненные API заказы из базы данных
            api_orders = self.db.get_api_orders()
            
            if api_orders:
                # Преобразуем объекты APIOrder в словари для отображения в таблице
                order_infos = []
                for api_order in api_orders:
                    order_info = {
                        "orderId": api_order.order_id,
                        "orderStatus": api_order.order_status,
                        "orderStatusDescription": api_order.order_status_description,
                        "createdTimestamp": api_order.created_timestamp,
                        "totalQuantity": api_order.total_quantity,
                        "numOfProducts": api_order.num_of_products,
                        "productGroupType": api_order.product_group_type,
                        "signed": api_order.signed,
                        "verified": api_order.verified,
                        "buffers": api_order.buffers
                    }
                    order_infos.append(order_info)
                
                # Обновляем таблицу API заказов
                self.view.update_api_orders_table(order_infos)
                logger.info(f"Загружено {len(order_infos)} API заказов из базы данных")
                
                # Находим, сколько из них устаревших
                obsolete_count = sum(1 for order in api_orders if order.order_status == "OBSOLETE")
                active_count = len(api_orders) - obsolete_count
                
                # Отображаем информацию в строке состояния
                status_message = f"Загружено {len(order_infos)} заказов из базы данных ("
                if active_count > 0:
                    status_message += f"{active_count} активных"
                if active_count > 0 and obsolete_count > 0:
                    status_message += ", "
                if obsolete_count > 0:
                    status_message += f"{obsolete_count} устаревших"
                status_message += "). Для обновления с сервера нажмите 'Обновить заказы'"
                
                self.view.set_api_orders_status(status_message)
            else:
                # Если нет данных, очищаем таблицу
                self.view.update_api_orders_table([])
                logger.info("API заказы не найдены в базе данных")
                
                # Отображаем информацию в строке состояния
                self.view.set_api_orders_status("API заказы не найдены в базе данных. Для загрузки с сервера нажмите 'Обновить заказы'")
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке API заказов из базы данных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке API заказов из базы данных: {str(e)}")
    
    def delete_api_order(self, order_id):
        """Удаление API заказа из базы данных"""
        try:
            self.db.delete_api_order(order_id)
            logger.info(f"API заказ с ID={order_id} успешно удален")
            self.view.show_message("Успех", f"API заказ с ID={order_id} успешно удален")
            
            # Обновление таблицы API заказов
            self.load_api_orders_from_db()
            
        except Exception as e:
            logger.error(f"Ошибка при удалении API заказа: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении API заказа: {str(e)}")
    
    def get_km_from_order(self, order_id, gtin, quantity):
        """Получение КМ из заказа
        
        Args:
            order_id (str): Идентификатор заказа
            gtin (str): GTIN товара
            quantity (int): Количество запрашиваемых кодов
            
        Returns:
            None: Метод отображает результат в интерфейсе
        """
        try:
            logger.info(f"Запрос на получение КМ из заказа: order_id={order_id}, gtin={gtin}, quantity={quantity}")
            
            # Вызываем метод API-клиента
            response = self.api_client.get_codes_from_order(
                order_id=order_id,
                gtin=gtin,
                quantity=quantity
            )
            
            # Логируем полный ответ для отладки
            logger.debug(f"Полный ответ от API: {response}")
            
            # Проверяем успешность выполнения запроса
            if response.get("success", False):
                # Получаем коды маркировки из ответа
                codes = response.get("codes", [])
                codes_count = len(codes)
                
                # Формируем сообщение
                message = f"Получено {codes_count} КМ из заказа {order_id}"
                
                # Если есть коды, отображаем их в представлении и сохраняем в БД
                if codes_count > 0:
                    # Проверяем существование таблицы marking_codes
                    cursor = self.db.conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='marking_codes'")
                    if not cursor.fetchone():
                        logger.error("Таблица marking_codes не существует. Создаем таблицу...")
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS marking_codes (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                code TEXT NOT NULL,
                                gtin TEXT NOT NULL,
                                order_id TEXT NOT NULL,
                                used INTEGER DEFAULT 0,
                                exported INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                        self.db.conn.commit()
                        logger.info("Таблица marking_codes создана")
                    
                    # Очищаем коды от возможных невалидных символов для БД
                    # Конвертируем контрольные символы в текстовое представление
                    processed_codes = []
                    for i, code in enumerate(codes):
                        # Логируем каждый код для отладки
                        logger.debug(f"Исходный код {i}: {repr(code)}")
                        
                        # Заменяем Group Separator (GS, ASCII 29, \u001d) на текстовое представление [GS]
                        processed_code = code.replace('\u001d', '[GS]')
                        
                        # Проверяем, что все непечатаемые символы заменены
                        if any(ord(c) < 32 for c in processed_code):
                            logger.warning(f"Код содержит непечатаемые символы после обработки: {repr(processed_code)}")
                            # Заменяем все непечатаемые символы на их представление
                            processed_code = ''.join(c if ord(c) >= 32 else f'[{ord(c)}]' for c in processed_code)
                            
                        processed_codes.append(processed_code)
                        logger.debug(f"Обработанный код {i}: {repr(processed_code)}")
                    
                    # Пробуем сохранить коды напрямую
                    try:
                        cursor = self.db.conn.cursor()
                        
                        # Подготавливаем данные для вставки
                        data = [(code, gtin, order_id) for code in processed_codes]
                        
                        # Выполняем вставку каждого кода по отдельности для лучшей диагностики
                        for i, (code, g, o_id) in enumerate(data):
                            try:
                                cursor.execute(
                                    "INSERT INTO marking_codes (code, gtin, order_id) VALUES (?, ?, ?)",
                                    (code, g, o_id)
                                )
                                logger.debug(f"Код {i} успешно вставлен в БД")
                            except Exception as e:
                                logger.error(f"Ошибка при вставке кода {i}: {str(e)}")
                        
                        self.db.conn.commit()
                        save_result = True
                        logger.info(f"Коды сохранены напрямую в базу данных: {len(processed_codes)} шт.")
                    except Exception as e:
                        logger.error(f"Ошибка при прямом сохранении кодов: {str(e)}")
                        
                        # Пробуем использовать метод из класса Database
                        save_result = self.db.save_marking_codes(processed_codes, gtin, order_id)
                    
                    if save_result:
                        message += " и сохранено в базу данных"
                        logger.info(f"Коды сохранены в базу данных для заказа {order_id}")
                    else:
                        message += ", но не удалось сохранить их в базу данных"
                        logger.warning(f"Не удалось сохранить коды в базу данных для заказа {order_id}")
                    
                    # Добавляем 2 потерянных кода вручную (если они были получены ранее)
                    if not save_result and len(codes) >= 2:
                        try:
                            # Сохраняем первые 2 кода в отдельный файл для восстановления
                            with open(f"recovered_codes_{order_id}.txt", "w", encoding="utf-8") as f:
                                for i, code in enumerate(codes[:2]):
                                    processed_code = code.replace('\u001d', '[GS]')
                                    f.write(f"{processed_code}\n")
                            logger.info(f"Сохранены 2 кода для восстановления в файл recovered_codes_{order_id}.txt")
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении кодов в файл: {str(e)}")
                    
                    # Отображаем коды в интерфейсе - для отображения используем исходные коды
                    self.view.display_codes_from_order(order_id, gtin, codes)
                    logger.info(message)
                    self.view.show_message("Успех", message)
                else:
                    logger.warning(f"Не удалось получить КМ из заказа {order_id}: коды отсутствуют в ответе")
                    self.view.show_message("Предупреждение", f"Не удалось получить КМ из заказа {order_id}: коды отсутствуют в ответе")
            else:
                # Получаем информацию об ошибке
                error_message = "Ошибка при получении КМ из заказа"
                if "globalErrors" in response:
                    error_message += ": " + ", ".join(response["globalErrors"])
                elif "error" in response:
                    if isinstance(response["error"], dict):
                        error_message += ": " + response["error"].get("message", "Неизвестная ошибка")
                    else:
                        error_message += ": " + str(response["error"])
                
                logger.error(error_message)
                self.view.show_message("Ошибка", error_message)
                
        except ValueError as e:
            # Обработка ошибок валидации параметров
            error_message = f"Ошибка валидации параметров: {str(e)}"
            logger.error(error_message)
            self.view.show_message("Ошибка", error_message)
            
        except requests.RequestException as e:
            # Обработка ошибок сети
            error_message = f"Ошибка сети при получении КМ из заказа: {str(e)}"
            logger.error(error_message)
            self.view.show_message("Ошибка", error_message)
            
        except Exception as e:
            # Обработка прочих ошибок
            import traceback
            error_message = f"Неизвестная ошибка при получении КМ из заказа: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            self.view.show_message("Ошибка", f"{error_message}\nПроверьте лог приложения для подробностей.")
    
    def save_all_data(self):
        """Сохранение всех данных перед завершением приложения"""
        try:
            logger.info("Сохранение данных перед выходом")
            if self.db:
                self.db.commit()
                logger.info("Данные успешно сохранены перед выходом")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных перед выходом: {str(e)}")
            
    def get_marking_codes(self, filters):
        """Получение кодов маркировки из базы данных
        
        Args:
            filters (dict): Фильтры для выборки кодов
                gtin (str, optional): Фильтр по GTIN
                order_id (str, optional): Фильтр по ID заказа
                used (bool, optional): Фильтр по использованным кодам
                exported (bool, optional): Фильтр по экспортированным кодам
        """
        try:
            logger.info(f"Запрос кодов маркировки с фильтрами: {filters}")
            
            # Сохраняем фильтры для последующего использования
            self._last_marking_codes_filters = filters
            
            # Получаем коды из базы данных
            codes = self.db.get_marking_codes(
                gtin=filters.get("gtin"),
                order_id=filters.get("order_id"),
                used=filters.get("used"),
                exported=filters.get("exported")
            )
            
            # Обновляем таблицу в интерфейсе
            self.view.update_marking_codes_table(codes)
            
            # Логируем результат
            logger.info(f"Получено {len(codes)} кодов маркировки")
            
        except Exception as e:
            logger.error(f"Ошибка при получении кодов маркировки: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при получении кодов маркировки: {str(e)}")
    
    def mark_codes_as_used(self, code_ids):
        """Отметка кодов маркировки как использованных
        
        Args:
            code_ids (List[int]): Список ID кодов для отметки
        """
        try:
            logger.info(f"Отметка кодов как использованных: {code_ids}")
            
            # Отмечаем коды как использованные
            result = self.db.mark_codes_as_used(code_ids)
            
            if result:
                logger.info(f"Успешно отмечено {len(code_ids)} кодов как использованные")
                self.view.show_message("Успех", f"Успешно отмечено {len(code_ids)} кодов как использованные")
                
                # Обновляем таблицу кодов маркировки
                last_filters = getattr(self, "_last_marking_codes_filters", {})
                self.get_marking_codes(last_filters)
            else:
                logger.error(f"Не удалось отметить коды как использованные")
                self.view.show_message("Ошибка", "Не удалось отметить коды как использованные")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке кодов как использованных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при отметке кодов как использованных: {str(e)}")
    
    def mark_codes_as_exported(self, code_ids):
        """Отметка кодов маркировки как экспортированных
        
        Args:
            code_ids (List[int]): Список ID кодов для отметки
        """
        try:
            logger.info(f"Отметка кодов как экспортированных: {code_ids}")
            
            # Отмечаем коды как экспортированные
            result = self.db.mark_codes_as_exported(code_ids)
            
            if result:
                logger.info(f"Успешно отмечено {len(code_ids)} кодов как экспортированные")
                self.view.show_message("Успех", f"Успешно отмечено {len(code_ids)} кодов как экспортированные")
                
                # Обновляем таблицу кодов маркировки
                last_filters = getattr(self, "_last_marking_codes_filters", {})
                self.get_marking_codes(last_filters)
            else:
                logger.error(f"Не удалось отметить коды как экспортированные")
                self.view.show_message("Ошибка", "Не удалось отметить коды как экспортированные")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке кодов как экспортированных: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при отметке кодов как экспортированных: {str(e)}")
    
    def load_marking_codes(self):
        """Загрузка кодов маркировки из базы данных"""
        try:
            # По умолчанию показываем только неиспользованные и неэкспортированные коды
            filters = {"used": False, "exported": False}
            self._last_marking_codes_filters = filters
            
            # Получаем коды из базы данных
            codes = self.db.get_marking_codes(**filters)
            
            # Обновляем таблицу в интерфейсе
            self.view.update_marking_codes_table(codes)
            logger.info(f"Таблица кодов маркировки обновлена, получено {len(codes)} записей")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке кодов маркировки: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке кодов маркировки: {str(e)}")

    # Методы для работы с файлами агрегации
    def load_aggregation_files(self):
        """Загрузка файлов агрегации из базы данных"""
        try:
            files = self.db.get_aggregation_files()
            self.view.update_aggregation_files_table(files)
            logger.info("Таблица файлов агрегации обновлена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке файлов агрегации: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке файлов агрегации: {str(e)}")

    def add_aggregation_file(self, filename: str, data: Dict, comment: str):
        """Добавление нового файла агрегации
        
        Args:
            filename (str): Имя файла
            data (Dict): Данные из JSON-файла
            comment (str): Комментарий к файлу
        """
        try:
            # Получаем название продукции
            product = data.get('NameProduct', "")
            # Если название продукции пустое, попробуем найти в других возможных полях
            if not product:
                # Проверяем другие возможные названия поля продукции
                possible_product_fields = ['nameProduct', 'productName', 'name', 'product', 'Product']
                for field in possible_product_fields:
                    if field in data and data[field]:
                        product = data[field]
                        logger.info(f"Найдено название продукции в поле '{field}': {product}")
                        break
                        
                # Если всё еще не нашли, попробуем поискать в глубине JSON
                if not product:
                    def find_product_name(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                key_lower = key.lower()
                                if 'product' in key_lower and 'name' in key_lower and isinstance(value, str):
                                    return value
                                elif key_lower in ['nameproduct', 'productname', 'name', 'product'] and isinstance(value, str):
                                    return value
                                
                                result = find_product_name(value, f"{path}.{key}" if path else key)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                result = find_product_name(item, f"{path}[{i}]")
                                if result:
                                    return result
                        return None
                        
                    product_from_search = find_product_name(data)
                    if product_from_search:
                        product = product_from_search
                        logger.info(f"Найдено название продукции при глубоком поиске: {product}")
            
            logger.info(f"Обработка файла агрегации: {filename}")
            logger.info(f"Название продукции: {product}")
            
            # Попробуем найти элементы разными способами
            marking_codes = []  # уровень 0
            level1_codes = []   # уровень 1
            level2_codes = []   # уровень 2
            
            # Для хранения всех кодов (для отметки использованных)
            all_codes = set()
            
            # Логирование ключей в JSON
            logger.info(f"Ключи в JSON: {list(data.keys())}")
            
            # Метод 1: Проверяем наличие поля 'items'
            items = data.get('items', [])
            if items and isinstance(items, list):
                logger.info(f"Найдено поле 'items' с {len(items)} элементами")
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    level = item.get('level', 0)
                    barcode = item.get('Barcode', '')
                    if barcode:
                        # Нормализуем формат кода - заменяем \u001d на [GS]
                        normalized_barcode = self.normalize_barcode(barcode)
                        all_codes.add(normalized_barcode)  # Добавляем в общий набор кодов
                        if level == 0:
                            marking_codes.append(normalized_barcode)
                        elif level == 1:
                            level1_codes.append(normalized_barcode)
                        elif level == 2:
                            level2_codes.append(normalized_barcode)
            
            # Если кодов всё ещё нет, попробуем другой метод
            if not marking_codes and not level1_codes and not level2_codes:
                # Метод 2: Проверяем каждый ключ в данных
                for key, value in data.items():
                    if isinstance(value, dict):
                        # Если значение - словарь, проверяем его поля
                        level = value.get('level', None)
                        barcode = value.get('Barcode', '')
                        if barcode and level is not None:
                            # Нормализуем формат кода
                            normalized_barcode = self.normalize_barcode(barcode)
                            all_codes.add(normalized_barcode)  # Добавляем в общий набор кодов
                            if level == 0:
                                marking_codes.append(normalized_barcode)
                            elif level == 1:
                                level1_codes.append(normalized_barcode)
                            elif level == 2:
                                level2_codes.append(normalized_barcode)
                    elif isinstance(value, list):
                        # Если значение - список, проверяем каждый элемент
                        for item in value:
                            if isinstance(item, dict):
                                level = item.get('level', None)
                                barcode = item.get('Barcode', '')
                                if barcode and level is not None:
                                    # Нормализуем формат кода
                                    normalized_barcode = self.normalize_barcode(barcode)
                                    all_codes.add(normalized_barcode)  # Добавляем в общий набор кодов
                                    if level == 0:
                                        marking_codes.append(normalized_barcode)
                                    elif level == 1:
                                        level1_codes.append(normalized_barcode)
                                    elif level == 2:
                                        level2_codes.append(normalized_barcode)
            
            # Если кодов все ещё нет, попробуем рекурсивный метод для поиска
            if not marking_codes and not level1_codes and not level2_codes:
                logger.info("Пробуем рекурсивный поиск Barcode и level")
                
                def search_in_json(obj, path=""):
                    if isinstance(obj, dict):
                        # Проверяем, есть ли в этом словаре Barcode и level
                        barcode = obj.get('Barcode', '')
                        level = obj.get('level', None)
                        if barcode and level is not None:
                            logger.info(f"Найден Barcode: {barcode}, level: {level} по пути {path}")
                            # Нормализуем формат кода
                            normalized_barcode = self.normalize_barcode(barcode)
                            all_codes.add(normalized_barcode)  # Добавляем в общий набор кодов
                            if level == 0:
                                marking_codes.append(normalized_barcode)
                            elif level == 1:
                                level1_codes.append(normalized_barcode)
                            elif level == 2:
                                level2_codes.append(normalized_barcode)
                        
                        # Проверяем вложенные элементы
                        for key, value in obj.items():
                            search_in_json(value, f"{path}.{key}" if path else key)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            search_in_json(item, f"{path}[{i}]")
                
                search_in_json(data)
            
            # Логирование результатов
            logger.info(f"Найдено кодов маркировки (уровень 0): {len(marking_codes)}")
            logger.info(f"Найдено кодов агрегации 1 уровня: {len(level1_codes)}")
            logger.info(f"Найдено кодов агрегации 2 уровня: {len(level2_codes)}")
            logger.info(f"Всего уникальных кодов: {len(all_codes)}")
            
            # Сохраняем полное содержимое JSON
            json_content = json.dumps(data)
            
            # Добавляем файл в базу данных
            file = self.db.add_aggregation_file(
                filename=filename,
                product=product,
                marking_codes=marking_codes,
                level1_codes=level1_codes,
                level2_codes=level2_codes,
                comment=comment,
                json_content=json_content
            )
            
            # Отмечаем коды как использованные в таблице "Коды маркировки"
            if all_codes:
                self.mark_codes_used_by_barcodes(list(all_codes))
            
            # Обновляем таблицу файлов агрегации
            self.load_aggregation_files()
            
            logger.info(f"Файл агрегации '{filename}' успешно добавлен")
            self.view.show_message("Успех", f"Файл агрегации '{filename}' успешно добавлен")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении файла агрегации: {str(e)}")
            logger.exception("Подробная информация об ошибке:")
            self.view.show_message("Ошибка", f"Ошибка при добавлении файла агрегации: {str(e)}")

    def normalize_barcode(self, barcode):
        """Нормализует формат штрих-кода, заменяя различные представления разделителя GS
        
        Args:
            barcode (str): Исходный штрих-код
            
        Returns:
            str: Нормализованный штрих-код
        """
        # Заменяем различные представления разделителя GS на [GS]
        normalized = barcode
        
        # Заменяем \u001d (unicode) на [GS]
        normalized = normalized.replace('\u001d', '[GS]')
        
        # Заменяем литеральную строку '\u001d' на [GS]
        normalized = normalized.replace('\\u001d', '[GS]')
        
        # Заменяем ASCII-код 29 (GS) на [GS]
        if '\x1d' in normalized:
            normalized = normalized.replace('\x1d', '[GS]')
        
        logger.debug(f"Нормализация штрих-кода: '{barcode}' -> '{normalized}'")
        return normalized

    def delete_aggregation_file(self, file_id: int):
        """Удаление файла агрегации
        
        Args:
            file_id (int): ID файла агрегации
        """
        try:
            # Получаем информацию о файле для сообщения
            file = self.db.get_aggregation_file_by_id(file_id)
            if not file:
                self.view.show_message("Ошибка", f"Файл агрегации с ID {file_id} не найден")
                return
            
            # Собираем все коды из файла
            all_codes = set()
            all_codes.update(file.marking_codes)
            all_codes.update(file.level1_codes)
            all_codes.update(file.level2_codes)
            
            # Удаляем файл из базы данных
            if self.db.delete_aggregation_file(file_id):
                # Отмечаем коды как неиспользованные в таблице "Коды маркировки"
                if all_codes:
                    self.unmark_codes_used_by_barcodes(list(all_codes))
                    
                # Обновляем таблицу файлов агрегации
                self.load_aggregation_files()
                
                logger.info(f"Файл агрегации '{file.filename}' успешно удален")
                self.view.show_message("Успех", f"Файл агрегации '{file.filename}' успешно удален")
            else:
                self.view.show_message("Ошибка", f"Не удалось удалить файл агрегации с ID {file_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении файла агрегации: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при удалении файла агрегации: {str(e)}")
        
    def mark_codes_used_by_barcodes(self, barcodes: List[str]):
        """Отметить коды маркировки как использованные по значению штрих-кода
        
        Args:
            barcodes (List[str]): Список штрих-кодов
        """
        try:
            # Получаем ID кодов маркировки по значениям штрих-кодов
            code_ids = self.db.get_marking_code_ids_by_barcodes(barcodes)
            
            if code_ids:
                logger.info(f"Найдено {len(code_ids)} кодов маркировки для отметки как использованные")
                # Отмечаем их как использованные
                self.mark_codes_as_used(code_ids)
            else:
                logger.info("Не найдено кодов маркировки для отметки как использованные")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке кодов как использованных по штрих-кодам: {str(e)}")
        
    def unmark_codes_used_by_barcodes(self, barcodes: List[str]):
        """Снять отметку 'использованные' с кодов маркировки по значению штрих-кода
        
        Args:
            barcodes (List[str]): Список штрих-кодов
        """
        try:
            # Получаем ID кодов маркировки по значениям штрих-кодов
            code_ids = self.db.get_marking_code_ids_by_barcodes(barcodes)
            
            if code_ids:
                logger.info(f"Найдено {len(code_ids)} кодов маркировки для снятия отметки 'использованные'")
                # Снимаем отметку 'использованные'
                self.db.unmark_codes_as_used(code_ids)
                # Обновляем таблицу кодов маркировки, если она открыта
                self.load_marking_codes()
            else:
                logger.info("Не найдено кодов маркировки для снятия отметки 'использованные'")
                
        except Exception as e:
            logger.error(f"Ошибка при снятии отметки 'использованные' с кодов по штрих-кодам: {str(e)}")

    def export_aggregation_file(self, file_id: int, export_path: str):
        """Экспорт файла агрегации в JSON-файл
        
        Args:
            file_id (int): ID файла агрегации
            export_path (str): Путь для сохранения файла
        """
        try:
            # Получаем файл агрегации по ID
            file = self.db.get_aggregation_file_by_id(file_id)
            if not file:
                self.view.show_message("Ошибка", f"Файл агрегации с ID {file_id} не найден")
                return False
            
            # Проверяем, есть ли содержимое JSON
            if not file.json_content:
                self.view.show_message("Ошибка", f"В файле агрегации '{file.filename}' отсутствует содержимое JSON")
                return False
            
            # Сохраняем содержимое JSON в файл
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(file.json_content)
            
            logger.info(f"Файл агрегации '{file.filename}' успешно экспортирован в '{export_path}'")
            self.view.show_message("Успех", f"Файл агрегации успешно экспортирован в '{export_path}'")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте файла агрегации: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при экспорте файла агрегации: {str(e)}")
            return False

    def get_aggregation_file_by_id(self, file_id: int):
        """Получение файла агрегации по ID
        
        Args:
            file_id (int): ID файла агрегации
            
        Returns:
            Optional[AggregationFile]: Объект файла агрегации или None
        """
        try:
            return self.db.get_aggregation_file_by_id(file_id)
        except Exception as e:
            logger.error(f"Ошибка при получении файла агрегации с ID={file_id}: {str(e)}")
            logger.exception("Подробная трассировка ошибки:")
            return None

    def send_utilisation_report(self, report_data):
        """Отправка отчета об использовании (нанесении) КМ"""
        try:
            # Проверяем наличие данных для отправки
            if not report_data or 'sntins' not in report_data or not report_data['sntins']:
                self.view.show_message("Ошибка", "Не выбраны коды маркировки для отчета")
                return
            
            # Проверяем наличие omsId в отчете
            if 'omsId' not in report_data or not report_data['omsId']:
                # Если omsId отсутствует, пытаемся его получить из настроек API-клиента
                if hasattr(self, 'api_client') and self.api_client and self.api_client.omsid:
                    report_data['omsId'] = self.api_client.omsid
                    logger.info(f"Добавлен omsId из API-клиента: {self.api_client.omsid}")
                else:
                    # Пытаемся получить omsId из базы данных
                    try:
                        credentials = self.db.get_credentials()
                        if credentials and len(credentials) > 0:
                            report_data['omsId'] = credentials[0].omsid
                            logger.info(f"Добавлен omsId из БД: {credentials[0].omsid}")
                    except Exception as e:
                        logger.error(f"Не удалось получить omsId из БД: {str(e)}")
            
            # Логирование данных отчета (только для отладки)
            logger.info(f"Отправка отчета о нанесении. Количество кодов: {len(report_data['sntins'])}")
            logger.info(f"Пример кода: {report_data['sntins'][0] if report_data['sntins'] else 'нет кодов'}")
            logger.info(f"Идентификатор СУЗ (omsId): {report_data.get('omsId', 'не указан')}")
            
            # Если omsId все еще отсутствует, выводим предупреждение
            if 'omsId' not in report_data or not report_data['omsId']:
                self.view.show_message(
                    "Предупреждение", 
                    "Отсутствует идентификатор СУЗ (omsId). Отчет может быть отклонен API. "
                    "Проверьте настройки учетных данных."
                )
                logger.warning("omsId не найден для отчета о нанесении!")
            
            # Отправляем отчет через API-клиент
            response = self.api_client.post_utilisation(report_data)
            
            # Обрабатываем ответ
            if response.get('success', False):
                # Если отчет успешно отправлен, отмечаем коды как использованные в БД
                # TODO: Реализовать отметку кодов как использованных
                
                self.view.show_message("Отчет о нанесении", "Отчет успешно отправлен")
            else:
                error_message = "Ошибка при отправке отчета"
                if 'fieldErrors' in response:
                    field_errors = []
                    for field_error in response['fieldErrors']:
                        field_errors.append(f"{field_error.get('fieldName')}: {field_error.get('fieldError')}")
                    error_message += ": " + ", ".join(field_errors)
                elif 'globalErrors' in response:
                    error_message += ": " + ", ".join(response['globalErrors'])
                elif 'error' in response and isinstance(response['error'], dict) and 'message' in response['error']:
                    error_message += ": " + response['error']['message']
                
                self.view.show_message("Ошибка", error_message)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке отчета: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось отправить отчет: {str(e)}")

    # Методы для работы с типами использования кодов маркировки
    def load_usage_types(self):
        """Загрузка типов использования кодов маркировки из базы данных"""
        try:
            # Получаем типы использования из базы данных
            usage_types = self.db.get_usage_types()
            logger.info(f"Загружено {len(usage_types)} типов использования кодов маркировки")
            return usage_types
        except Exception as e:
            logger.error(f"Ошибка при загрузке типов использования кодов маркировки: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось загрузить типы использования кодов маркировки: {str(e)}")
            return []
    
    def add_usage_type(self, code, name, description=None):
        """Добавление типа использования кодов маркировки"""
        try:
            logger.info(f"Запрос на добавление типа использования: code='{code}', name='{name}', description='{description}'")
            
            # Проверка входных данных
            if not code or not code.strip():
                logger.error("Код типа использования не может быть пустым")
                self.view.show_message("Ошибка", "Код типа использования не может быть пустым")
                return False
                
            if not name or not name.strip():
                logger.error("Название типа использования не может быть пустым")
                self.view.show_message("Ошибка", "Название типа использования не может быть пустым")
                return False
            
            # Проверяем наличие таблицы usage_types
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_types'")
                if not cursor.fetchone():
                    logger.warning("Таблица usage_types не существует. Создаем таблицу...")
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS usage_types (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            code TEXT NOT NULL UNIQUE,
                            name TEXT NOT NULL,
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    self.db.conn.commit()
                    logger.info("Таблица usage_types успешно создана")
            except Exception as e:
                logger.error(f"Ошибка при проверке/создании таблицы usage_types: {str(e)}")
            
            # Вызываем метод базы данных для добавления типа использования
            usage_type_id = self.db.add_usage_type(code, name, description)
            
            if usage_type_id > 0:
                logger.info(f"Тип использования кодов маркировки успешно добавлен: ID={usage_type_id}")
                
                # Обновляем таблицу типов использования в представлении
                self.load_usage_types()
                
                self.view.show_message("Успех", f"Тип использования '{name}' успешно добавлен")
                return True
            else:
                logger.error("Ошибка при добавлении типа использования")
                self.view.show_message("Ошибка", "Не удалось добавить тип использования")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении типа использования: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось добавить тип использования: {str(e)}")
            return False
    
    def update_usage_type(self, usage_type_id, code, name, description=None):
        """Обновление типа использования кодов маркировки"""
        try:
            # Обновляем тип использования в базе данных
            if self.db.update_usage_type(usage_type_id, code, name, description):
                logger.info(f"Обновлен тип использования кодов маркировки: {name} ({code})")
                self.view.show_message("Успех", "Тип использования успешно обновлен")
                return True
            else:
                logger.error(f"Ошибка при обновлении типа использования кодов маркировки: {name} ({code})")
                self.view.show_message("Ошибка", "Не удалось обновить тип использования")
                return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении типа использования кодов маркировки: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось обновить тип использования: {str(e)}")
            return False
    
    def delete_usage_type(self, usage_type_id):
        """Удаление типа использования кодов маркировки"""
        try:
            # Удаляем тип использования из базы данных
            if self.db.delete_usage_type(usage_type_id):
                logger.info(f"Удален тип использования кодов маркировки с ID: {usage_type_id}")
                self.view.show_message("Успех", "Тип использования успешно удален")
                return True
            else:
                logger.error(f"Ошибка при удалении типа использования кодов маркировки с ID: {usage_type_id}")
                self.view.show_message("Ошибка", "Не удалось удалить тип использования")
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении типа использования кодов маркировки: {str(e)}")
            self.view.show_message("Ошибка", f"Не удалось удалить тип использования: {str(e)}")
            return False

    def load_api_orders(self, *args):
        """Загрузка API заказов с сервера"""
        try:
            logger.info("Загрузка API заказов с сервера")
            
            # Проверяем соединение с API
            if not self.check_api_availability():
                logger.warning("API недоступен, используем локальные данные")
                # Загружаем данные из базы
                self.load_api_orders_from_db()
                return
            
            # Получаем заказы через API-клиент
            response = self.api_client.get_orders()
            
            if response and 'data' in response and isinstance(response['data'], list):
                try:
                    # Преобразуем данные в объекты APIOrder
                    api_orders = []
                    
                    for order_data in response['data']:
                        try:
                            order = APIOrder(
                                order_id=order_data.get('orderId', ''),
                                order_status=order_data.get('orderStatus', ''),
                                created_timestamp=order_data.get('createdTimestamp', ''),
                                total_quantity=order_data.get('totalQuantity', 0),
                                num_of_products=order_data.get('numOfProducts', 0),
                                product_group_type=order_data.get('productGroupType', ''),
                                signed=order_data.get('signed', False),
                                verified=order_data.get('verified', False),
                                buffers=order_data.get('buffers', [])
                            )
                            api_orders.append(order)
                        except Exception as e:
                            logger.error(f"Ошибка при преобразовании данных заказа: {str(e)}")
                    
                    # Сохраняем заказы в базу данных
                    saved_orders = self.db.save_api_orders(api_orders)
                    
                    # Обновляем представление
                    self.view.update_api_orders_table(saved_orders)
                    
                    logger.info(f"Загружено {len(saved_orders)} API заказов")
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке API заказов: {str(e)}")
                    self.view.show_message("Ошибка", f"Ошибка при обработке API заказов: {str(e)}")
            else:
                logger.warning("Некорректный формат ответа от API")
                self.view.show_message("Ошибка", "Некорректный формат ответа от API")
                
                # Загружаем данные из базы как запасной вариант
                self.load_api_orders_from_db()
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке API заказов: {str(e)}")
            self.view.show_message("Ошибка", f"Ошибка при загрузке API заказов: {str(e)}")
            
            # Загружаем данные из базы как запасной вариант
            self.load_api_orders_from_db()
    
    def check_api_availability(self):
        """Проверка доступности API"""
        try:
            # Проверяем активное подключение
            active_connection = self.db.get_active_connection()
            if not active_connection:
                logger.warning("Отсутствует активное подключение")
                return False
            
            # Пытаемся выполнить простой запрос для проверки соединения
            response = self.api_client.ping()
            
            # Если получен ответ с кодом 200, API доступен
            return response is not None and response.get('success', False)
            
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности API: {str(e)}")
            return False