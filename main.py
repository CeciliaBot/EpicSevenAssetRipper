import os
import sys
import pathlib
from PyQt5                  import QtWidgets, QtGui, QtCore
from ui.window              import AppWindow
from app.constants          import APP_NAME, VERSION
import qdarktheme


class APP():
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        qdarktheme.setup_theme()
        self.window = AppWindow(VERSION)
        self.window.setWindowTitle(APP_NAME + ' ' + VERSION)
        self.window.setWindowIcon(QtGui.QIcon("./ui/assets/icon.png"))
        self.window.setWindowFlags(QtCore.Qt.Window)

if __name__ == "__main__":

    pathlib.Path(os.path.join(os.getcwd(), 'data.pack')).mkdir(parents=True, exist_ok=True)

    app = APP()

    print(APP_NAME, VERSION)

    app.window.show()
    sys.exit(app.app.exec_())