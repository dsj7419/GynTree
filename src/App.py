"""
GynTree: This is the main entry point for the GynTree application.
It initializes the core components and starts the user interface.
The App module orchestrates the overall flow of the application,
connecting various components and services.
"""

from PyQt5.QtWidgets import QApplication
from controllers.AppController import AppController

def main():
    app = QApplication([])

    controller = AppController()
    controller.run()

    app.exec_()

if __name__ == '__main__':
    main()
