# GynTree: Implements functionality to export directory trees as images or ASCII text.

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication, QTreeWidget, QTreeWidgetItem, QHeaderView, QTreeWidgetItemIterator
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor

class TreeExporter:
    def __init__(self, tree_widget):
        self.tree_widget = tree_widget

    def export_as_image(self):
        """
        Export the full directory tree as a PNG image with correct column positioning.
        """
        file_name, _ = QFileDialog.getSaveFileName(None, 'Export as PNG', '', 'PNG Files (*.png)')
        if not file_name:
            return

        temp_tree = QTreeWidget()
        temp_tree.setColumnCount(self.tree_widget.columnCount())
        temp_tree.setHeaderLabels([self.tree_widget.headerItem().text(i) for i in range(self.tree_widget.columnCount())])

        self._copy_items(self.tree_widget.invisibleRootItem(), temp_tree.invisibleRootItem())

        temp_tree.expandAll()

        temp_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
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

  
        total_height += 50 

        pixmap = QPixmap(total_width, total_height)
        pixmap.fill(Qt.white)

        temp_tree.setFixedSize(total_width, total_height)
        temp_tree.setStyleSheet("background-color: white;")

        painter = QPainter(pixmap)
        temp_tree.render(painter)
        painter.end()

        pixmap.save(file_name)
        QMessageBox.information(None, 'Export Successful', f'Directory tree exported as {file_name}')

    def _copy_items(self, source_item, target_item):
        """
        Recursively copy items from source tree to target tree.
        """
        for i in range(source_item.childCount()):
            child = source_item.child(i)
            new_item = QTreeWidgetItem(target_item)
            for j in range(self.tree_widget.columnCount()):
                new_item.setText(j, child.text(j))
                new_item.setIcon(j, child.icon(j))
            self._copy_items(child, new_item)

    def export_as_ascii(self):
        """
        Export the directory tree as ASCII text format.
        """
        file_name, _ = QFileDialog.getSaveFileName(None, 'Export as ASCII', '', 'Text Files (*.txt)')
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                self._write_ascii_tree(f)
            QMessageBox.information(None, 'Export Successful', f'Directory tree exported as {file_name}')

    def _write_ascii_tree(self, file):
        """
        Write the directory tree to the file in ASCII format.
        """
        for i in range(self.tree_widget.topLevelItemCount()):
            self._write_tree_item(file, self.tree_widget.topLevelItem(i), 0)

    def _write_tree_item(self, file, item, indent):
        """
        Recursively write the tree structure to a file in ASCII format.
        """
        prefix = '│  ' * indent
        connector = '├─ ' if indent > 0 else ''
        
        file.write(f"{prefix}{connector}{item.text(0)}\n")
        for i in range(item.childCount()):
            self._write_tree_item(file, item.child(i), indent + 1)