import PyInstaller.__main__
import os
import sys
from PyQt5.QtCore import QLibraryInfo

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Get PyQt5 directory
pyqt_dir = QLibraryInfo.location(QLibraryInfo.BinariesPath)

# List of QT DLLs we need
qt_dlls = ['Qt5Core.dll', 'Qt5Gui.dll', 'Qt5Widgets.dll']

# Prepare the command line arguments for PyInstaller
pyinstaller_args = [
    '--name=GynTree',
    '--windowed',
    '--onefile',
    f'--icon={os.path.join(project_root, "assets", "images", "GynTree_logo 64X64.ico")}',
    f'--add-data={os.path.join(project_root, "assets")};assets',
    '--hidden-import=PyQt5.sip',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
]

# Add Qt DLLs
for dll in qt_dlls:
    dll_path = os.path.join(pyqt_dir, dll)
    if os.path.exists(dll_path):
        pyinstaller_args.append(f'--add-binary={dll_path};PyQt5/Qt/bin/')
    else:
        print(f"Warning: {dll} not found in {pyqt_dir}")

# Add the main script
pyinstaller_args.append(os.path.join(project_root, 'src', 'App.py'))

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_args)