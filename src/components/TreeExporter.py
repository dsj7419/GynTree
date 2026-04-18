import logging
import os
import shutil
import tempfile
import time
from typing import List, Optional, TextIO, Tuple

from PyQt5.QtCore import QMutex, QMutexLocker, Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
)

logger = logging.getLogger(__name__)


class TreeExporter:
    def __init__(self, tree_widget: QTreeWidget) -> None:
        if not isinstance(tree_widget, QTreeWidget):
            raise ValueError("TreeExporter requires a valid QTreeWidget instance")

        self.tree_widget = tree_widget
        self._mutex = QMutex()
        self._temp_files: List[str] = []
        self._max_retries = 3
        self._retry_delay = 0.5

    def __del__(self) -> None:
        self._cleanup_temp_files()

    def _cleanup_temp_files(self) -> None:
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")
        self._temp_files.clear()

    def export_as_image(self) -> bool:
        with QMutexLocker(self._mutex):
            try:
                if self.tree_widget.topLevelItemCount() == 0:
                    QMessageBox.warning(
                        None, "Export Failed", "Cannot export an empty directory tree."
                    )
                    return False

                file_name, _ = QFileDialog.getSaveFileName(
                    None, "Export PNG", "", "PNG Files (*.png)"
                )

                if not file_name:
                    return False

                temp_tree = self._create_temp_tree()
                if not temp_tree:
                    return False

                dimensions = self._calculate_tree_dimensions(temp_tree)
                if not dimensions:
                    return False

                total_width, total_height = dimensions
                success = self._render_and_save_pixmap(
                    temp_tree, total_width, total_height, file_name
                )

                if success:
                    QMessageBox.information(
                        None,
                        "Export Successful",
                        f"Directory tree exported to {file_name}",
                    )
                    return True
                return False

            except Exception as e:
                logger.error(f"Failed to export image: {str(e)}")
                QMessageBox.critical(
                    None, "Export Failed", "Failed to export directory tree as image"
                )
                return False

    def _create_temp_tree(self) -> Optional[QTreeWidget]:
        try:
            temp_tree = QTreeWidget()
            header_item = self.tree_widget.headerItem()
            if header_item:
                temp_tree.setColumnCount(self.tree_widget.columnCount())
                temp_tree.setHeaderLabels(
                    [header_item.text(i) for i in range(self.tree_widget.columnCount())]
                )
                self._copy_items(
                    self.tree_widget.invisibleRootItem(), temp_tree.invisibleRootItem()
                )
                temp_tree.expandAll()
                temp_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
                return temp_tree
            return None
        except Exception as e:
            logger.error(f"Failed to create temporary tree: {str(e)}")
            return None

    def _calculate_tree_dimensions(
        self, temp_tree: QTreeWidget
    ) -> Optional[Tuple[int, int]]:
        try:
            name_column_width = temp_tree.header().sectionSize(0)
            type_column_width = max(temp_tree.header().sectionSize(1), 100)

            temp_tree.setColumnWidth(0, name_column_width + 20)
            temp_tree.setColumnWidth(1, type_column_width)

            total_width = name_column_width + type_column_width + 40
            total_height = 0

            iterator = QTreeWidgetItemIterator(
                temp_tree,
                QTreeWidgetItemIterator.IteratorFlags(QTreeWidgetItemIterator.All),
            )
            item = iterator.value()
            while item:
                total_height += temp_tree.visualItemRect(item).height()
                iterator += 1  # type: ignore
                item = iterator.value()

            return total_width, total_height + 50
        except Exception as e:
            logger.error(f"Failed to calculate tree dimensions: {str(e)}")
            return None

    def _render_and_save_pixmap(
        self,
        temp_tree: QTreeWidget,
        total_width: int,
        total_height: int,
        file_name: str,
    ) -> bool:
        temp_file = None
        try:
            pixmap = QPixmap(total_width, total_height)
            pixmap.fill(Qt.white)

            temp_tree.setFixedSize(total_width, total_height)
            temp_tree.setStyleSheet("background-color: white;")

            painter = QPainter(pixmap)
            temp_tree.render(painter)
            painter.end()

            temp_suffix = os.urandom(6).hex()
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{temp_suffix}.png"
            )
            temp_file_path = temp_file.name
            temp_file.close()
            self._temp_files.append(temp_file_path)

            if not pixmap.save(temp_file_path):
                logger.error("Failed to save pixmap to temporary file")
                return False

            target_dir = os.path.dirname(file_name)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            if os.path.exists(file_name):
                os.remove(file_name)

            shutil.copy2(temp_file_path, file_name)
            return True

        except Exception as e:
            logger.error(f"Failed to render and save pixmap: {str(e)}")
            return False
        finally:
            self._cleanup_temp_files()

    def _copy_items(
        self, source_item: QTreeWidgetItem, target_item: QTreeWidgetItem
    ) -> None:
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

    def export_as_ascii(self) -> bool:
        with QMutexLocker(self._mutex):
            try:
                file_name, _ = QFileDialog.getSaveFileName(
                    None, "Export ASCII", "", "Text Files (*.txt)"
                )

                if not file_name:
                    return False

                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", delete=False, suffix=".txt", encoding="utf-8"
                )
                self._temp_files.append(temp_file.name)

                with open(temp_file.name, "w", encoding="utf-8") as f:
                    self._write_ascii_tree(f)

                for attempt in range(self._max_retries):
                    try:
                        target_dir = os.path.dirname(file_name)
                        if target_dir:
                            os.makedirs(target_dir, exist_ok=True)

                        if os.path.exists(file_name):
                            os.remove(file_name)

                        shutil.copy2(temp_file.name, file_name)

                        if temp_file.name in self._temp_files:
                            self._temp_files.remove(temp_file.name)

                        QMessageBox.information(
                            None,
                            "Export Successful",
                            f"Directory tree exported to {file_name}",
                        )
                        return True

                    except Exception as e:
                        if attempt < self._max_retries - 1:
                            logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
                            time.sleep(self._retry_delay)
                        else:
                            logger.error(
                                f"Failed to save ASCII file after {self._max_retries} "
                                f"attempts: {e}"
                            )
                            QMessageBox.critical(
                                None,
                                "Export Failed",
                                "Failed to export directory tree as ASCII",
                            )
                            return False

            except Exception as e:
                logger.error(f"Failed to export ASCII: {str(e)}")
                QMessageBox.critical(
                    None, "Export Failed", "Failed to export directory tree as ASCII"
                )
                return False
            finally:
                self._cleanup_temp_files()
                return False

    def _write_ascii_tree(self, file: TextIO) -> None:
        try:
            if self.tree_widget.topLevelItemCount() > 0:
                root_item = self.tree_widget.topLevelItem(0)
                if root_item:
                    text = root_item.text(0)
                    if text:  # Add null check
                        file.write(f"{text}\n")
                        last_indices: List[bool] = []
                        for i in range(root_item.childCount()):
                            is_last = i == root_item.childCount() - 1
                            child = root_item.child(i)
                            if child:  # Add null check
                                self._write_tree_item(
                                    file, child, "", is_last, last_indices
                                )
        except Exception as e:
            logger.error(f"Failed to write ASCII tree: {str(e)}")
            raise

    def _write_tree_item(
        self,
        file: TextIO,
        item: QTreeWidgetItem,
        prefix: str,
        is_last: bool,
        last_indices: List[bool],
    ) -> None:
        try:
            branch = "└── " if is_last else "├── "
            vertical = "    " if is_last else "│   "

            file.write(f"{prefix}{branch}{item.text(0)}\n")
            new_prefix = prefix + vertical

            child_count = item.childCount()
            for i in range(child_count):
                child_is_last = i == child_count - 1
                self._write_tree_item(
                    file,
                    item.child(i),
                    new_prefix,
                    child_is_last,
                    last_indices + [is_last],
                )

        except Exception as e:
            logger.error(f"Failed to write tree item: {str(e)}")
            raise
