import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from views.main_window import MainWindow
from models.database import Database
from models.api_client import APIClient
from controllers.main_controller import MainController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Точка входа в приложение"""
    try:
        logger.info("Запуск приложения")
        
        # Создание приложения PyQt
        app = QApplication(sys.argv)
        
        # Создание базы данных
        db = Database()
        
        # Создание API-клиента с передачей базы данных для логирования
        api_client = APIClient(db=db)
        
        # Создание главного окна
        view = MainWindow()
        
        # Создание контроллера
        controller = MainController(view, db, api_client)
        
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