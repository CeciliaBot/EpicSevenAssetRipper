from PyQt5.QtCore                           import QObject, QThread, pyqtSignal
from app.utils_generate_file_tree_pack      import generate_pack_tree

class GenerateTreeThread(QThread): # QObject
    # started = pyqtSignal() no need for start (QThread provides basic)
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    path = None
    decrypted = None

    def __init__(self, parent=None) -> None:
        QThread.__init__(self, parent=parent)

    def updateData(self, path, decrypted):
        self.path = path
        self.decrypted = decrypted

    def run(self):
        # self.started.emit()
        res = generate_pack_tree(self.path, self.decrypted, self.progress.emit)
        self.finished.emit(res)