import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from components.UI.animated_toggle import AnimatedToggle
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from components.UI.ProjectManagementUI import ProjectManagementUI
from components.UI.ProjectUI import ProjectUI
from components.UI.ResultUI import ResultUI
from models.Project import Project
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.ProjectContext import ProjectContext
from services.SettingsManager import SettingsManager
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

if TYPE_CHECKING:
    from controllers.AppController import AppController

logger = logging.getLogger(__name__)


class DashboardUI(QMainWindow):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)
    theme_changed = pyqtSignal(str)

    def __init__(self, controller: "AppController") -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = ThemeManager.getInstance()
        self.project_ui: Optional[ProjectUI] = None
        self.result_ui: Optional[ResultUI] = None
        self.auto_exclude_ui: Optional[AutoExcludeUI] = None
        self.exclusions_ui: Optional[ExclusionsManagerUI] = None
        self.directory_tree_ui: Optional[DirectoryTreeUI] = None
        self.theme_toggle: Optional[AnimatedToggle] = None
        self._welcome_label: Optional[QLabel] = None
        self.ui_components: List[Optional[QWidget]] = []
        self.initUI()

    def initUI(self) -> None:
        self.setWindowTitle("GynTree Dashboard")
        icon_path = get_resource_path("assets/images/GynTree_logo.ico")
        self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        theme_toggle_layout = QHBoxLayout()
        self.theme_toggle = AnimatedToggle(
            checked_color="#FFB000", pulse_checked_color="#44FFB000"
        )
        self.theme_toggle.setFixedSize(self.theme_toggle.sizeHint())
        current_theme = self.theme_manager.get_current_theme()
        self.theme_toggle.setChecked(current_theme == "dark")
        self.theme_toggle.stateChanged.connect(self.on_theme_toggle_changed)
        self.theme_toggle.setVisible(True)
        self.theme_toggle.setEnabled(True)
        theme_toggle_layout.addStretch()
        theme_toggle_layout.addWidget(self.theme_toggle)
        main_layout.addLayout(theme_toggle_layout)

        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_path = get_resource_path("assets/images/gyntree_logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            logger.warning(f"Logo file not found at {logo_path}")

        self._welcome_label = QLabel("Welcome to GynTree!")
        self._welcome_label.setFont(QFont("Arial", 24, QFont.Bold))

        header_layout.addWidget(logo_label)
        header_layout.addWidget(self._welcome_label)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

        self.projects_btn = self.create_styled_button("Create New/Open a Project")
        self.manage_projects_btn = self.create_styled_button("Manage Projects")
        self.manage_exclusions_btn = self.create_styled_button("Manage Exclusions")
        self.analyze_directory_btn = self.create_styled_button("Analyze Directory")
        self.view_directory_tree_btn = self.create_styled_button("View Directory Tree")

        self.manage_exclusions_btn.setEnabled(False)
        self.analyze_directory_btn.setEnabled(False)
        self.view_directory_tree_btn.setEnabled(False)

        for btn in [
            self.projects_btn,
            self.manage_projects_btn,
            self.manage_exclusions_btn,
            self.analyze_directory_btn,
            self.view_directory_tree_btn,
        ]:
            main_layout.addWidget(btn)

        self.projects_btn.clicked.connect(self.show_project_ui)
        self.manage_projects_btn.clicked.connect(self.controller.manage_projects)
        self.manage_exclusions_btn.clicked.connect(self.controller.manage_exclusions)
        self.analyze_directory_btn.clicked.connect(self.controller.analyze_directory)
        self.view_directory_tree_btn.clicked.connect(
            self.controller.view_directory_tree
        )

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.setGeometry(300, 300, 800, 600)
        self.theme_manager.apply_theme(self)

    def create_styled_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        font = QFont("Arial")
        font.setPointSize(14)
        btn.setFont(font)
        return btn

    def on_theme_toggle_changed(self, state: bool) -> None:
        new_theme = "dark" if state else "light"
        self.theme_manager.set_theme(new_theme)
        self.theme_manager.apply_theme(self)
        self.theme_changed.emit(new_theme)

    def toggle_theme(self) -> None:
        new_theme = self.theme_manager.toggle_theme()
        if self.theme_toggle:
            self.theme_toggle.setChecked(new_theme == "dark")
        self.theme_changed.emit(new_theme)

    def show_dashboard(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def show_project_ui(self) -> Optional[ProjectUI]:
        if self.project_ui:
            self.project_ui.close()
            self.project_ui = None

        self.project_ui = ProjectUI(self.controller)
        self.project_ui.project_created.connect(self.on_project_created)
        self.project_ui.project_loaded.connect(self.on_project_loaded)
        self.ui_components.append(self.project_ui)
        self.project_ui.show()
        return self.project_ui

    def show_project_management(self) -> ProjectManagementUI:
        management_ui = ProjectManagementUI(self.controller, self.theme_manager)
        self.ui_components.append(management_ui)
        management_ui.show()
        return management_ui

    def on_project_created(self, project: Project) -> None:
        logger.info(f"Project creation signal received: {project.name}")
        self.controller.on_project_created(project)
        self.update_project_info(project)

    def on_project_loaded(self, project: Project) -> None:
        self.update_project_info(project)

    def show_auto_exclude_ui(
        self,
        auto_exclude_manager: AutoExcludeManager,
        settings_manager: SettingsManager,
        formatted_recommendations: Dict[str, Set[str]],
        project_context: ProjectContext,
    ) -> Optional[AutoExcludeUI]:
        mock_exclude_ui = getattr(self, "_mock_auto_exclude_ui", None)
        if mock_exclude_ui:
            mock_exclude_ui.show()
            return mock_exclude_ui

        self.auto_exclude_ui = AutoExcludeUI(
            auto_exclude_manager,
            settings_manager,
            formatted_recommendations,
            project_context,
        )
        self.ui_components.append(self.auto_exclude_ui)
        self.auto_exclude_ui.show()
        return self.auto_exclude_ui

    def show_result(self, directory_analyzer: DirectoryAnalyzer) -> Optional[ResultUI]:
        mock_result_ui = getattr(self, "_mock_result_ui", None)
        if mock_result_ui:
            mock_result_ui.show()
            return mock_result_ui

        if self.controller.project_controller.project_context:
            self.result_ui = ResultUI(
                self.controller, self.theme_manager, directory_analyzer
            )
            self.ui_components.append(self.result_ui)
            self.result_ui.show()
            return self.result_ui
        return None

    def manage_exclusions(
        self, settings_manager: SettingsManager
    ) -> Optional[ExclusionsManagerUI]:
        mock_exclusions_ui = getattr(self, "_mock_exclusions_ui", None)
        if mock_exclusions_ui:
            mock_exclusions_ui.show()
            return mock_exclusions_ui

        if self.controller.project_controller.project_context:
            self.exclusions_ui = ExclusionsManagerUI(
                self.controller, self.theme_manager, settings_manager
            )
            self.ui_components.append(self.exclusions_ui)
            self.exclusions_ui.show()
            return self.exclusions_ui

        QMessageBox.warning(
            self,
            "No Project",
            "Please load or create a project before managing exclusions.",
        )
        return None

    def view_directory_tree_ui(
        self, result: Dict[str, Any]
    ) -> Optional[DirectoryTreeUI]:
        mock_tree_ui = getattr(self, "_mock_directory_tree_ui", None)
        if mock_tree_ui:
            mock_tree_ui.update_tree(result)
            mock_tree_ui.show()
            return mock_tree_ui

        if not self.directory_tree_ui:
            self.directory_tree_ui = DirectoryTreeUI(
                self.controller, self.theme_manager
            )
        self.directory_tree_ui.update_tree(result)
        self.ui_components.append(self.directory_tree_ui)
        self.directory_tree_ui.show()
        return self.directory_tree_ui

    def update_project_info(self, project: Project) -> None:
        self.setWindowTitle(f"GynTree - {project.name}")
        status_msg = f"Current project: {project.name}, Start directory: {project.start_directory}"
        if hasattr(project, "status"):
            status_msg = f"{status_msg} - {project.status}"
        self.status_bar.showMessage(status_msg)
        self.enable_project_actions()

    def enable_project_actions(self) -> None:
        self.manage_exclusions_btn.setEnabled(True)
        self.analyze_directory_btn.setEnabled(True)
        self.view_directory_tree_btn.setEnabled(True)

    def clear_directory_tree(self) -> None:
        if hasattr(self, "directory_tree_view"):
            self.directory_tree_view.clear()
        logger.debug("Directory tree cleared")

    def clear_analysis(self) -> None:
        if hasattr(self, "analysis_result_view"):
            self.analysis_result_view.clear()
        logger.debug("Analysis results cleared")

    def clear_exclusions(self) -> None:
        if hasattr(self, "exclusions_list_view"):
            self.exclusions_list_view.clear()
        logger.debug("Exclusions list cleared")

    def show_error_message(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        for component in self.ui_components:
            try:
                if component and hasattr(component, "close"):
                    component.close()
            except Exception as e:
                logger.debug(f"Non-critical UI component cleanup warning: {e}")
        super().closeEvent(event)
