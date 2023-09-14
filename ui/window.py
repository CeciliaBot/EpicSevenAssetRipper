from PyQt5            import QtWidgets, QtCore
from .header_tabs     import createTabs

class AppWindow(QtWidgets.QMainWindow):
    def __init__(self, version: float, parent=None) -> None:
        QtWidgets.QWidget.__init__(self, parent)

        self.version = version
        self.resize(900, 700)

        ## layout = QtWidgets.QVBoxLayout()
        ## self.setLayout(layout)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setEnabled(True)
        self.tabs.setObjectName("tabs")

        ##layout.addWidget(self.tabs)
        self.setCentralWidget(self.tabs)

        self.tabList = createTabs(self, self.tabs)