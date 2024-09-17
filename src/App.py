# GynTree: This is the main entry point for the GynTree application. It initializes the core components and starts the user interface.

from PyQt5.QtWidgets import QApplication
from controllers.AppController import AppController

def main():
    # Initialize the QApplication here to ensure it exists before creating any UI elements
    app = QApplication([])

    # Initialize the controller and run the app
    controller = AppController()
    controller.run()

    # Start the QApplication event loop
    app.exec_()

if __name__ == '__main__':
    main()
