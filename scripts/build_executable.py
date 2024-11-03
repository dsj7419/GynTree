import os
import sys

import PyInstaller.__main__
from PyQt5.QtCore import QLibraryInfo

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

pyqt_dir = QLibraryInfo.location(QLibraryInfo.BinariesPath)

qt_dlls = ["Qt5Core.dll", "Qt5Gui.dll", "Qt5Widgets.dll"]

pyinstaller_args = [
    "--name=GynTree",
    "--windowed",
    "--onefile",
    "--clean",
    f'--icon={os.path.join(project_root, "assets", "images", "GynTree_logo.ico")}',  # For EXE icon
    f'--add-data={os.path.join(project_root, "assets", "images", "GynTree_logo.ico")};assets/images',  # For use in app
    f'--add-data={os.path.join(project_root, "assets", "images", "file_icon.png")};assets/images',
    f'--add-data={os.path.join(project_root, "assets", "images", "folder_icon.png")};assets/images',
    f'--add-data={os.path.join(project_root, "assets", "images", "GynTree_logo.png")};assets/images',
    f'--add-data={os.path.join(project_root, "src", "styles", "light_theme.qss")};styles',
    f'--add-data={os.path.join(project_root, "src", "styles", "dark_theme.qss")};styles',
    "--hidden-import=PyQt5.sip",
    "--hidden-import=PyQt5.QtCore",
    "--hidden-import=PyQt5.QtGui",
    "--hidden-import=PyQt5.QtWidgets",
]

for dll in qt_dlls:
    dll_path = os.path.join(pyqt_dir, dll)
    if os.path.exists(dll_path):
        pyinstaller_args.append(f"--add-binary={dll_path};PyQt5/Qt/bin/")
    else:
        print(f"Warning: {dll} not found in {pyqt_dir}")

pyinstaller_args.append(os.path.join(project_root, "src", "App.py"))

PyInstaller.__main__.run(pyinstaller_args)
