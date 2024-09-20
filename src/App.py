""" 
    GynTree: Main entry point for the GynTree application. Initializes core components and starts the user interface. 
    The app module orchestrates the overall flow of the application, connecting various components and services.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from controllers.AppController import AppController
from utilities.error_handler import ErrorHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Set global exception handling
    sys.excepthook = ErrorHandler.global_exception_handler

    app = QApplication(sys.argv)
    controller = AppController()

    # Connect cleanup method to be called on application quit
    app.aboutToQuit.connect(controller.cleanup)

    # Start the application
    controller.run()

    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
        sys.exit(1)
