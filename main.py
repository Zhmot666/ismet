import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from views.main_window import MainWindow
from models.database import Database
from models.api_client import APIClient
from models.api_log import APILog
from controllers.main_controller import MainController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Класс для обработки завершения приложения
class ApplicationManager(QObject):
    aboutToQuit = pyqtSignal()
    
    def __init__(self, db):
        super().__init__()
        self.db = db
    
    def setup_quit_handler(self, app):
        app.aboutToQuit.connect(self.handle_quit)
    
    def handle_quit(self):
        logger.info("Приложение завершает работу, сохранение данных...")
        try:
            # Явное сохранение данных перед выходом
            if self.db:
                self.db.commit()
                logger.info("Данные успешно сохранены перед выходом")
            self.aboutToQuit.emit()
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных перед выходом: {str(e)}")

def main():
    """Точка входа в приложение"""
    try:
        logger.info("Запуск приложения")
        
        # Создание базы данных
        db = Database()
        
        # Проверяем и восстанавливаем стандартные статусы заказов
        if db.insert_default_order_statuses():
            logger.info("Восстановлены отсутствующие стандартные статусы заказов")
        
        # Создание приложения PyQt
        app = QApplication(sys.argv)
        
        # Создание менеджера приложения для обработки выхода
        app_manager = ApplicationManager(db)
        app_manager.setup_quit_handler(app)
        
        # Создание объекта логирования API
        api_logger = APILog(db=db)
        
        # Создание API-клиента с передачей логгера для логирования
        api_client = APIClient(db=db, api_logger=api_logger)
        
        # Создание главного окна
        view = MainWindow()
        
        # Создание контроллера с передачей логгера API
        controller = MainController(view, db, api_client, api_logger)
        
        # Устанавливаем ссылку на контроллер в главном окне
        view.controller = controller
        
        # Подключение сигнала завершения к методу сохранения данных
        app_manager.aboutToQuit.connect(controller.save_all_data)
        
        # Отображение главного окна
        view.show()
        
        logger.info("Приложение инициализировано")
        
        # Запуск цикла обработки событий
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {str(e)}")
        QMessageBox.critical(None, "Ошибка", f"Ошибка при запуске приложения: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 