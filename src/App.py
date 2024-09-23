import sys
import logging
from PyQt5.QtWidgets import QApplication
from controllers.AppController import AppController
from utilities.error_handler import ErrorHandler
from utilities.theme_manager import ThemeManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    sys.excepthook = ErrorHandler.global_exception_handler

    app = QApplication(sys.argv)

    theme_manager = ThemeManager.getInstance()

    try:
        controller = AppController()
    except Exception as e:
        logger.critical(f"Failed to initialize AppController: {str(e)}")
        sys.exit(1)

    app.aboutToQuit.connect(controller.cleanup)

    controller.run()

    theme_manager.apply_theme_to_all_windows(app)

    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
        sys.exit(1)