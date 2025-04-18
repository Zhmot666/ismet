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
        """Подключение сигналов и слотов"""
        # Сигналы вкладки заказов
        self.view.add_order_signal.connect(self.add_order)
        self.view.ping_signal.connect(self.check_api)
        self.view.get_orders_signal.connect(self.get_orders)
        self.view.get_report_signal.connect(self.get_report)
        self.view.get_version_signal.connect(self.get_version)
        self.view.get_orders_status_signal.connect(self.get_orders_status)
        self.view.create_emission_order_signal.connect(self.create_emission_order)
        self.view.get_order_details_signal.connect(self.get_order_details)
        self.view.api_orders_signal.connect(self.get_api_orders)
        self.view.delete_api_order_signal.connect(self.delete_api_order)
        self.view.get_km_from_order_signal.connect(self.get_km_from_order)
        
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
        
        # Сигналы для работы со статусами заказов
        self.view.load_order_statuses_signal.connect(self.load_order_statuses)
        self.view.add_order_status_signal.connect(self.add_order_status)
        self.view.edit_order_status_signal.connect(self.edit_order_status)
        self.view.delete_order_status_signal.connect(self.delete_order_status)
        
        # Сигналы для работы с кодами маркировки
        self.view.get_marking_codes_signal.connect(self.get_marking_codes)
        self.view.mark_codes_as_used_signal.connect(self.mark_codes_as_used)
        self.view.mark_codes_as_exported_signal.connect(self.mark_codes_as_exported)
    
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