import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class AutoExcludeWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, project_context):
        super().__init__()
        self.project_context = project_context

    def run(self):
        try:
            logger.debug("Auto-exclusion analysis started.")
            self._validate_context()
            formatted_recommendations = self._perform_analysis()
            logger.debug("Auto-exclusion analysis completed.")
            self.finished.emit(formatted_recommendations)
            return formatted_recommendations
        except Exception as e:
            error_msg = self._handle_error(e)
            self.error.emit(error_msg)
            raise Exception(error_msg)

    def _perform_analysis(self):
        recommendations = self.project_context.trigger_auto_exclude()
        if not recommendations:
            logger.info("No new exclusions suggested.")
            return []
        return recommendations.split('\n')

    def _validate_context(self):
        if not self.project_context or not self.project_context.settings_manager:
            raise ValueError("ProjectContext or SettingsManager not properly initialized")

    def _handle_error(self, exception):
        error_msg = f"Error in auto-exclusion analysis: {str(exception)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg