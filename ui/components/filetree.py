import os
import math
from PyQt5              import QtCore
from PyQt5.QtWidgets    import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QVBoxLayout, QVBoxLayout
from PyQt5.QtCore       import Qt
from PyQt5.QtGui        import QIcon, QColor
from app.utils          import convert_size

class TreeTable:
    contextMenuOptions = []
    functionColumnContentItem = None

    def __init__(self):
        self.folderIcon = QIcon( os.path.join( os.getcwd(), 'ui', 'assets', 'folder.png'))
        self.fileIcon = QIcon( os.path.join( os.getcwd(), 'ui', 'assets', 'file.png'))
        self.tree = QTreeWidget()
        self.tree.setColumnWidth(0,300)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

    def widget(self):
        return self.tree

    def showTree(self, tree_map):
        self.tree.clear()
        self.addItems(self.tree, tree_map)
        self.treeData = tree_map

    def setColumns(self, columns):
        self.tree.setColumnCount(len(columns))
        self.tree.setHeaderLabels(columns)

    def setDictToColumn(self, fun):
        self.functionColumnContentItem = fun

    def getSelectedItemData(self):
        g = self.tree.currentItem()
        if g:
            return g.____data
        return None

    def getCurrentTreeData(self):
        return self.treeData

    def addItems(self, parent, items):
        items.sort(key=self.sortByType, reverse=True)
        for item in items:
            try:
                treeitem = QTreeWidgetItem(parent)
                treeitem.setTextAlignment( 1, 2 )
                treeitem.setTextAlignment( 2, 2 )
                treeitem.setTextAlignment( 3, 2 )
                treeitem.____data = item

                row = self.functionColumnContentItem(item)

                if "color" in item:
                    treeitem.setForeground(0, QColor(item["color"]))

                for index, key in enumerate(row):
                    if key is None:
                        continue

                    treeitem.setText(index, key)
                    
                if item["type"] == "folder":
                    treeitem.setIcon(0, self.folderIcon )
                    self.addItems(treeitem, item["children"])

            except:
                pass
            '''
            treeitem.setText(0, item["name"])
            treeitem.setText(2, convert_size(item["size"]))
            if item["type"] == "file":
                treeitem.setText(1, item["format"].upper())
                treeitem.setText(3, str(item["offset"]))
                # treeitem.setIcon(0, self.fileIcon )
            else:
                treeitem.setIcon(0, self.folderIcon )
                treeitem.setText(1, "Folder")
                # treeitem.setBackground(1, QColor("red"));
                treeitem.setText(3, str(item["files"]))
                self.addItems(treeitem, item["children"])
            '''

    def setContextMenu(self, options):
        self.contextMenuOptions = options

    # the function to display context menu
    def _show_context_menu(self, position):
        menu = QMenu(self.tree)
        for option in self.contextMenuOptions:
            op = QAction(option[0])
            op.triggered.connect(lambda: self.runContextOption(option[1]) )
            menu.addAction(op)

        menu.exec_(self.tree.mapToGlobal(position))

    # the action executed when menu is clicked
    def runContextOption(self, func):
        # column = self.tree.currentColumn()
        item = self.tree.currentItem()
        func(item.____data)

    @staticmethod
    def sortByType(item):
        return item["type"]
