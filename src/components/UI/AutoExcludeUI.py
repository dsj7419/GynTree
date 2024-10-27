from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget,
                             QTreeWidget, QTreeWidgetItem, QMessageBox, QHeaderView, QHBoxLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
import os
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class AutoExcludeUI(QMainWindow):
    def __init__(self, auto_exclude_manager, settings_manager, formatted_recommendations, project_context):
        super().__init__()
        self.auto_exclude_manager = auto_exclude_manager
        self.settings_manager = settings_manager
        self.formatted_recommendations = formatted_recommendations
        self.project_context = project_context
        self.theme_manager = ThemeManager.getInstance()

        self.folder_icon = QIcon(get_resource_path("../assets/images/folder_icon.png"))
        self.file_icon = QIcon(get_resource_path("../assets/images/file_icon.png"))

        self.setWindowTitle('Auto-Exclude Recommendations')
        self.setWindowIcon(QIcon(get_resource_path('../assets/images/GynTree_logo.ico')))

        self.init_ui()
        
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        title_label = QLabel('Auto-Exclude Recommendations', font=QFont('Arial', 16, QFont.Bold))
        header_layout.addWidget(title_label)

        collapse_btn = QPushButton('Collapse All')
        expand_btn = QPushButton('Expand All')
        header_layout.addWidget(collapse_btn)
        header_layout.addWidget(expand_btn)
        main_layout.addLayout(header_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name', 'Type'])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setIconSize(QSize(20, 20))
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.tree_widget)

        self.populate_tree()

        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        expand_btn.clicked.connect(self.tree_widget.expandAll)

        apply_button = QPushButton('Apply Exclusions')
        apply_button.clicked.connect(self.apply_exclusions)
        main_layout.addWidget(apply_button, alignment=Qt.AlignCenter)

        self.setCentralWidget(central_widget)
        self.setGeometry(300, 150, 800, 600)

        self.apply_theme()

    def populate_tree(self):
        """Populates the tree with merged exclusions from both AutoExcludeManager and project folder."""
        self.tree_widget.clear()
        root = self.tree_widget.invisibleRootItem()

        combined_exclusions = self.get_combined_exclusions()

        categories = ['root_exclusions', 'excluded_dirs', 'excluded_files']
        for category in categories:
            category_item = QTreeWidgetItem(root, [category.replace('_', ' ').title(), ''])
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsUserCheckable)

            for path in sorted(combined_exclusions.get(category, [])):
                item = QTreeWidgetItem(category_item, [path, category[:-1]])
                item.setIcon(0, self.folder_icon if os.path.isdir(path) else self.file_icon)
                if category != 'root_exclusions':
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.Checked)

        self.tree_widget.expandAll()

    def get_combined_exclusions(self):
        """Retrieve exclusions from AutoExcludeManager and merge with project exclusions."""
        manager_recommendations = self.auto_exclude_manager.get_recommendations()

        root_exclusions = set(self.project_context.settings_manager.get_root_exclusions())
        excluded_dirs = set(self.project_context.settings_manager.get_excluded_dirs())
        excluded_files = set(self.project_context.settings_manager.get_excluded_files())

        combined_exclusions = {
            'root_exclusions': manager_recommendations.get('root_exclusions', set()) | root_exclusions,
            'excluded_dirs': manager_recommendations.get('excluded_dirs', set()) | excluded_dirs,
            'excluded_files': manager_recommendations.get('excluded_files', set()) | excluded_files
        }

        return combined_exclusions

    def apply_exclusions(self):
        self.auto_exclude_manager.apply_recommendations()
        QMessageBox.information(self, "Exclusions Updated", "Exclusions have been successfully updated.")
        self.close()

    def update_recommendations(self, formatted_recommendations):
        self.formatted_recommendations = formatted_recommendations
        self.populate_tree()

    def apply_theme(self):
        self.theme_manager.apply_theme(self)

    def closeEvent(self, event):
        super().closeEvent(event)