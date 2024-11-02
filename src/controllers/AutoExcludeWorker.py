import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class AutoExcludeWorker(QObject):
    """Core worker class for thread-safe auto-exclusion analysis."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, project_context):
        super().__init__()
        if not project_context:
            raise ValueError("Project context cannot be None")
        self._project_context = project_context
        self._is_running = False
    
    def run(self):
        if self._is_running:
            return None
        
        self._is_running = True
        try:
            logger.debug("Auto-exclusion analysis started.")
            self._validate_context()
            result = self._perform_analysis()
            logger.debug("Auto-exclusion analysis completed.")
            self.finished.emit(result)
            return result
        except Exception as e:
            error_msg = self._handle_error(e)
            self.error.emit(error_msg)
            return None
        finally:
            self._is_running = False
    
    def _perform_analysis(self):
        recommendations = self._project_context.trigger_auto_exclude()
        if not recommendations:
            return []
            
        if isinstance(recommendations, str):
            return [recommendations]
        elif isinstance(recommendations, list):
            return recommendations
        return [str(recommendations)]
    
    def _validate_context(self):
        if not self._project_context or not hasattr(self._project_context, 'settings_manager'):
            raise ValueError("ProjectContext or SettingsManager not properly initialized")
    
    def _handle_error(self, exception):
        error_msg = f"Error in auto-exclusion analysis: {str(exception)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg