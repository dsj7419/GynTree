# GynTree: Implements functionality to export directory trees as images or ascii text.
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QApplication, QTreeWidget,
                           QTreeWidgetItem, QHeaderView, QTreeWidgetItemIterator)
from PyQt5.QtCore import Qt, QSize, QMutex, QMutexLocker
from PyQt5.QtGui import QPixmap, QPainter, QColor
import os
import logging
import tempfile
from pathlib import Path
import shutil
import time

logger = logging.getLogger(__name__)

class TreeExporter:
    """
    Handles exporting directory trees as images or ascii text with proper
    error handling and resource management.
    """
    def __init__(self, tree_widget):
        """
        Initialize TreeExporter with proper error checking.

        Args:
            tree_widget (QTreeWidget): The tree widget to export
        Raises:
            ValueError: If tree_widget is None or not a QTreeWidget
        """
        if not isinstance(tree_widget, QTreeWidget):
            raise ValueError("TreeExporter requires a valid QTreeWidget instance")
        
        self.tree_widget = tree_widget
        self._mutex = QMutex()  # For thread safety
        self._temp_files = []  # Track temporary resources
        self._max_retries = 3  # Maximum number of retries for file operations
        self._retry_delay = 0.5  # Delay between retries in seconds

    def __del__(self):
        """Cleanup temporary resources upon deletion"""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Clean up any temporary files created during export."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")
        self._temp_files.clear()

    def export_as_image(self):
        with QMutexLocker(self._mutex):
            try:
                if self.tree_widget.topLevelItemCount() == 0:
                    QMessageBox.warning(
                        None,
                        'Export Failed',
                        'Cannot export an empty directory tree.'
                    )
                    return False

                file_name, _ = QFileDialog.getSaveFileName(
                    None,
                    'Export PNG',
                    '',
                    'PNG Files (*.png)'
                )

                if not file_name:
                    return False

                # Create temporary tree widget
                temp_tree = self._create_temp_tree()
                if not temp_tree:
                    return False

                # Calculate dimensions
                dimensions = self._calculate_tree_dimensions(temp_tree)
                if not dimensions:
                    return False

                total_width, total_height = dimensions

                # Create and save pixmap
                success = self._render_and_save_pixmap(
                    temp_tree,
                    total_width,
                    total_height,
                    file_name
                )

                if success:
                    QMessageBox.information(
                        None,
                        'Export Successful',
                        f'Directory tree exported to {file_name}'
                    )
                    return True

                return False

            except Exception as e:
                logger.error(f"Failed to export image: {str(e)}")
                QMessageBox.critical(
                    None,
                    'Export Failed',
                    'Failed to export directory tree as image'
                )
                return False

    def _create_temp_tree(self):
        """
        Create a temporary tree widget for export.

        Returns:
            QTreeWidget: Temporary tree widget or None if creation fails
        """
        try:
            temp_tree = QTreeWidget()
            temp_tree.setColumnCount(self.tree_widget.columnCount())
            temp_tree.setHeaderLabels([
                self.tree_widget.headerItem().text(i)
                for i in range(self.tree_widget.columnCount())
            ])

            self._copy_items(
                self.tree_widget.invisibleRootItem(),
                temp_tree.invisibleRootItem()
            )

            temp_tree.expandAll()
            temp_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            return temp_tree

        except Exception as e:
            logger.error(f"Failed to create temporary tree: {str(e)}")
            return None

    def _calculate_tree_dimensions(self, temp_tree):
        """
        Calculate dimensions needed for the exported image.

        Args:
            temp_tree (QTreeWidget): Temporary tree widget

        Returns:
            tuple: (width, height) or None if calculation fails
        """
        try:
            name_column_width = temp_tree.header().sectionSize(0)
            type_column_width = max(temp_tree.header().sectionSize(1), 100)

            temp_tree.setColumnWidth(0, name_column_width + 20)
            temp_tree.setColumnWidth(1, type_column_width)

            total_width = name_column_width + type_column_width + 40
            total_height = 0

            iterator = QTreeWidgetItemIterator(temp_tree, QTreeWidgetItemIterator.All)
            while iterator.value():
                total_height += temp_tree.visualItemRect(iterator.value()).height()
                iterator += 1

            return total_width, total_height + 50

        except Exception as e:
            logger.error(f"Failed to calculate tree dimensions: {str(e)}")
            return None

    def _render_and_save_pixmap(self, temp_tree, total_width, total_height, file_name):
        """
        Render tree to pixmap and save it.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            pixmap = QPixmap(total_width, total_height)
            pixmap.fill(Qt.white)

            temp_tree.setFixedSize(total_width, total_height)
            temp_tree.setStyleSheet("background-color: white;")

            painter = QPainter(pixmap)
            temp_tree.render(painter)
            painter.end()

            # Create temporary file with a random suffix
            temp_suffix = os.urandom(6).hex()
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'_{temp_suffix}.png'
            )
            self._temp_files.append(temp_file.name)
            temp_file.close()

            # Save to temporary file
            if not pixmap.save(temp_file.name):
                logger.error("Failed to save pixmap to temporary file")
                return False

            # Attempt to move the file to final location with retries
            for attempt in range(self._max_retries):
                try:
                    # Ensure target directory exists
                    target_dir = os.path.dirname(file_name)
                    if target_dir:
                        os.makedirs(target_dir, exist_ok=True)

                    # If target file exists, try to remove it
                    if os.path.exists(file_name):
                        os.remove(file_name)

                    # Copy the file instead of moving it
                    shutil.copy2(temp_file.name, file_name)
                    
                    # Only remove from tracking if successful
                    if temp_file.name in self._temp_files:
                        self._temp_files.remove(temp_file.name)
                    
                    return True

                except Exception as e:
                    if attempt < self._max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
                        time.sleep(self._retry_delay)
                    else:
                        logger.error(f"Failed to save pixmap after {self._max_retries} attempts: {str(e)}")
                        return False

        except Exception as e:
            logger.error(f"Failed to render and save pixmap: {str(e)}")
            return False

        finally:
            # Ensure temporary files are cleaned up
            self._cleanup_temp_files()

    def _copy_items(self, source_item, target_item):
        """
        Recursively copy items from source tree to target tree with error handling.

        Args:
            source_item (QTreeWidgetItem): Source item to copy
            target_item (QTreeWidgetItem): Target item to copy to
        """
        try:
            for i in range(source_item.childCount()):
                child = source_item.child(i)
                new_item = QTreeWidgetItem(target_item)

                for j in range(self.tree_widget.columnCount()):
                    new_item.setText(j, child.text(j))
                    if not child.icon(j).isNull():
                        new_item.setIcon(j, child.icon(j))

                self._copy_items(child, new_item)

        except Exception as e:
            logger.error(f"Failed to copy tree items: {str(e)}")
            raise

    def export_as_ascii(self):
        """
        Export directory tree as ascii text format with proper error handling and beautiful formatting.

        Returns:
            bool: True if export successful, False otherwise
        """
        with QMutexLocker(self._mutex):
            try:
                file_name, _ = QFileDialog.getSaveFileName(
                    None,
                    'Export ASCII',
                    '',
                    'Text Files (*.txt)'
                )

                if not file_name:
                    return False

                # Write to temporary file first
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    delete=False,
                    suffix='.txt',
                    encoding='utf-8'
                )
                self._temp_files.append(temp_file.name)

                with open(temp_file.name, 'w', encoding='utf-8') as f:
                    self._write_ascii_tree(f)

                # Attempt to move to final location with retries
                for attempt in range(self._max_retries):
                    try:
                        # Ensure target directory exists
                        target_dir = os.path.dirname(file_name)
                        if target_dir:
                            os.makedirs(target_dir, exist_ok=True)

                        # If target file exists, try to remove it
                        if os.path.exists(file_name):
                            os.remove(file_name)

                        # Copy the file instead of moving it
                        shutil.copy2(temp_file.name, file_name)
                        
                        # Only remove from tracking if successful
                        if temp_file.name in self._temp_files:
                            self._temp_files.remove(temp_file.name)

                        QMessageBox.information(
                            None,
                            'Export Successful',
                            f'Directory tree exported to {file_name}'
                        )
                        return True

                    except Exception as e:
                        if attempt < self._max_retries - 1:
                            logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
                            time.sleep(self._retry_delay)
                        else:
                            logger.error(f"Failed to save ASCII file after {self._max_retries} attempts: {str(e)}")
                            QMessageBox.critical(
                                None,
                                'Export Failed',
                                'Failed to export directory tree as ASCII'
                            )
                            return False

            except Exception as e:
                logger.error(f"Failed to export ASCII: {str(e)}")
                QMessageBox.critical(
                    None,
                    'Export Failed',
                    'Failed to export directory tree as ASCII'
                )
                return False
            finally:
                # Ensure temporary files are cleaned up
                self._cleanup_temp_files()

    def _write_ascii_tree(self, file):
        """
        Write directory tree to file in ASCII format with error handling.

        Args:
            file: File object to write to
        """
        try:
            # Write root item
            if self.tree_widget.topLevelItemCount() > 0:
                root_item = self.tree_widget.topLevelItem(0)
                file.write(f"{root_item.text(0)}\n")
                
                # Process children with proper indentation and connectors
                last_indices = []
                for i in range(root_item.childCount()):
                    is_last = i == root_item.childCount() - 1
                    self._write_tree_item(file, root_item.child(i), "", is_last, last_indices)

        except Exception as e:
            logger.error(f"Failed to write ASCII tree: {str(e)}")
            raise

    def _write_tree_item(self, file, item, prefix, is_last, last_indices):
        """
        Recursively write tree structure to file in ASCII format with beautiful connectors.

        Args:
            file: File object to write to
            item (QTreeWidgetItem): Item to write
            prefix (str): Current line prefix
            is_last (bool): Whether this is the last item in current level
            last_indices (list): Track which levels are last items
        """
        try:
            # Define box drawing characters
            branch = "└── " if is_last else "├── "
            vertical = "    " if is_last else "│   "

            # Write current item
            file.write(f"{prefix}{branch}{item.text(0)}\n")

            # Calculate new prefix for children
            new_prefix = prefix + vertical

            # Process children
            child_count = item.childCount()
            for i in range(child_count):
                child_is_last = i == child_count - 1
                self._write_tree_item(
                    file,
                    item.child(i),
                    new_prefix,
                    child_is_last,
                    last_indices + [is_last]
                )

        except Exception as e:
            logger.error(f"Failed to write tree item: {str(e)}")
            raise