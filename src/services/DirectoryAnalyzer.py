import logging
from typing import Dict, Any
from services.DirectoryStructureService import DirectoryStructureService
import threading

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DirectoryAnalyzer:
    def __init__(self, start_dir: str, settings_manager):
        self.start_dir = start_dir
        self.directory_structure_service = DirectoryStructureService(settings_manager)
        self._stop_event = threading.Event()

    def analyze_directory(self) -> Dict[str, Any]:
        """
        Analyze directory and return hierarchical structure.
        """
        logger.debug(f"Analyzing directory hierarchy for: {self.start_dir}")
        return self.directory_structure_service.get_hierarchical_structure(self.start_dir, self._stop_event)

    def get_flat_structure(self) -> Dict[str, Any]:
        """
        Get flat structure of directory.
        """
        logger.debug(f"Generating flat directory structure for: {self.start_dir}")
        return self.directory_structure_service.get_flat_structure(self.start_dir, self._stop_event)

    def stop(self):
        """
        Signal analysis to stop.
        """
        self._stop_event.set()