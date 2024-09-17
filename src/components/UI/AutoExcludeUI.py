# GynTree: Defines the user interface for managing automatic file and directory exclusions.

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QLabel, QCheckBox, QPushButton,
                             QScrollArea, QWidget, QHBoxLayout, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
import os
from utilities.resource_path import get_resource_path

class AutoExcludeUI(QMainWindow):
    def __init__(self, auto_exclude_manager, settings_manager, formatted_recommendations):
        super().__init__()
        self.auto_exclude_manager = auto_exclude_manager
        self.settings_manager = settings_manager
        self.formatted_recommendations = formatted_recommendations
        self.checkboxes = {'directories': {}, 'files': {}}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Auto-Exclude Recommendations')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo 64X64.ico')))
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QLabel { font-size: 16px; color: #333; margin-bottom: 10px; }
            QCheckBox { font-size: 14px; color: #555; padding: 2px 0; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QPushButton { background-color: #4CAF50; color: white; padding: 10px 20px; 
                          font-size: 16px; margin: 4px 2px; border-radius: 8px; }
            QPushButton:hover { background-color: #45a049; }
            QTextEdit { font-size: 14px; color: #333; background-color: #fff; border: 1px solid #ddd; }
        """)

        main_layout = QVBoxLayout()
        title = QLabel('Auto-Exclude Recommendations')
        title.setFont(QFont('Arial', 18, QFont.Bold))
        main_layout.addWidget(title)

        recommendations_text = QTextEdit()
        recommendations_text.setPlainText(self.formatted_recommendations)
        recommendations_text.setReadOnly(True)
        recommendations_text.setFixedHeight(200)
        main_layout.addWidget(recommendations_text)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        current_settings = {
            'excluded_dirs': self.settings_manager.get_excluded_dirs(),
            'excluded_files': self.settings_manager.get_excluded_files()
        }
        recommendations = self.auto_exclude_manager.get_grouped_recommendations(self.settings_manager.settings)

        for exclusion_type in ['directories', 'files']:
            if recommendations[exclusion_type]:
                group_widget = QWidget()
                group_layout = QVBoxLayout(group_widget)
                group_checkbox = QCheckBox(exclusion_type.capitalize())
                group_checkbox.setFont(QFont('Arial', 14, QFont.Bold))
                group_checkbox.setChecked(True)
                group_checkbox.stateChanged.connect(lambda state, g=exclusion_type: self.toggle_group(state, g))
                self.checkboxes[exclusion_type]['group'] = group_checkbox
                group_layout.addWidget(group_checkbox)

                for item in recommendations[exclusion_type]:
                    item_checkbox = QCheckBox(os.path.basename(item))
                    item_checkbox.setChecked(True)
                    item_checkbox.setStyleSheet("margin-left: 20px;")
                    self.checkboxes[exclusion_type][item] = item_checkbox
                    group_layout.addWidget(item_checkbox)
                scroll_layout.addWidget(group_widget)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        apply_button = QPushButton('Apply')
        apply_button.clicked.connect(self.apply_exclusions)
        main_layout.addWidget(apply_button, alignment=Qt.AlignCenter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setGeometry(300, 300, 400, 600)

    def toggle_group(self, state, group):
        is_checked = (state == Qt.Checked)
        for item, checkbox in self.checkboxes[group].items():
            if item != 'group':
                checkbox.setChecked(is_checked)

    def apply_exclusions(self):
        current_settings = self.settings_manager.settings
        excluded_dirs = set(current_settings.get('excluded_dirs', []))
        excluded_files = set(current_settings.get('excluded_files', []))

        for exclusion_type, items in self.checkboxes.items():
            for item, checkbox in items.items():
                if checkbox.isChecked() and item != 'group':
                    if exclusion_type == 'directories':
                        excluded_dirs.add(item)
                    else:
                        excluded_files.add(item)

        self.settings_manager.update_settings({
            'excluded_dirs': list(excluded_dirs),
            'excluded_files': list(excluded_files)
        })
        self.close()

    def update_recommendations(self, formatted_recommendations):
        self.formatted_recommendations = formatted_recommendations
        recommendations_text = self.findChild(QTextEdit)
        if recommendations_text:
            recommendations_text.setPlainText(self.formatted_recommendations)