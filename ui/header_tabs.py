from PyQt5        import QtWidgets, QtCore, QtGui
import ui.tabs.FileTree.elements
import ui.tabs.DecryptExtract.main
import ui.tabs.credits.elements

def createTabs(self, parent):
        fileTab = ui.tabs.FileTree.elements.TreeTab()
        parent.addTab(fileTab.ui(), "File Tree")

        fileTab = ui.tabs.DecryptExtract.main.Main()
        parent.addTab(fileTab.ui(), "Decrypt")

        self.credits_tab = QtWidgets.QWidget()
        self.credits_tab.setObjectName("credits_tab")
        parent.addTab(self.credits_tab, "Credits")

        ui.tabs.credits.elements.create(self, self.credits_tab)


        return []