from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox
from ProgressBar import ProgressBar
import sys, time

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 button - pythonspot.com'
        self.left = 200
        self.top = 200
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button = QPushButton('PyQt5 button', self)
        button.setToolTip('This is an example button')
        button.move(100, 70)
        button.clicked.connect(self.on_click)

        self.show()

    def on_click(self):
        pb = ProgressBar()
        pb.setInfo("Extracting: cut/fhd/c1002_s3_1.png")

        for i in range(0, 2000):
            time.sleep(0.05)
            pb.setValue(((i + 1) / 2000) * 100)
            QApplication.processEvents()

        pb.close()

        QMessageBox.information(self, "Message", "Data Loaded")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())