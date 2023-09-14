from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from .ProgressBar_ui import Ui_Form

class ProgressBar(QtWidgets.QDialog, Ui_Form):
    def __init__(self, desc = None, parent=None):
        super(ProgressBar, self).__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setupUi(self)
        self.show()

        if desc != None:
            self.setDescription(desc)

    def setValue(self, val): # Sets value
        self.progressBar.setProperty("value", val)

    def setDescription(self, desc): # Sets Pbar window title
        self.setWindowTitle(desc)

    def setInfo(self, text):
        self.progress_info_label.setText(text)

def main():
    app = QtWidgets.QApplication(sys.argv)      # A new instance of QApplication
    form = ProgressBar('pbar')                        # We set the form to be our MainWindow (design)
    app.exec_()                                 # and execute the app

if __name__ == '__main__':                      # if we're running file directly and not importing it
    main()                                      # run the main function
