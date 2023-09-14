import os
from PyQt5 import QtWidgets, QtCore, QtGui
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from app.utils import checkValidDataPack
from ui.threads import Worker, ThreadPool
from app.fullyDecryptPack import decrypt, extract

class Main(QtWidgets.QWidget):
    def __init__(self):
        QtCore.QObject.__init__(self)

        # self.threadpool = QtCore.QThreadPool()
        self.is_decrypting = False
        self.is_extracting = False
        self.pack_file = None
        self.pack_decrypted_pack = None
        self.destination_file = None # Decrypted file
        self.destination_folder = None # Extract files to

        self.disable_while_decrypring = []
        self.disable_if_no_pack_file = []
        self.disable_while_extracting = []
        self.disable_if_no_pack_decrypted_pack = []

        main_layout = QtWidgets.QVBoxLayout()
        line1_layout = QtWidgets.QHBoxLayout()
        line2_layout = QtWidgets.QHBoxLayout()
        checkbox_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(line1_layout)
        main_layout.addLayout(line2_layout)
        main_layout.addLayout(checkbox_layout)
        main_layout.addStretch()
        main_layout.setSpacing(40)
        line1_layout.setSpacing(10)
        line2_layout.setSpacing(10)

        btn = QtWidgets.QPushButton("Decrypt")
        btn.pressed.connect(lambda: self.selectInputDecryption()) ###### buttons don't connect if the first button is not lambda?????
        btn.setFixedSize(150, 40)
        line1_layout.addWidget(btn)
        self.disable_while_decrypring.append(btn)

        btn = QtWidgets.QPushButton("Select output file")
        btn.pressed.connect(self.selectOutputDecryption)
        btn.setFixedSize(150, 40)
        line1_layout.addWidget(btn)
        self.disable_while_decrypring.append(btn)

        self.btn_decrypt_go = QtWidgets.QPushButton("GO!")
        self.btn_decrypt_go.setFixedSize(40, 40)
        self.btn_decrypt_go.pressed.connect(self.decryptGoClick)
        line1_layout.addWidget(self.btn_decrypt_go)
        self.disable_while_decrypring.append(self.btn_decrypt_go)

        self.progressbar_decrypt = QtWidgets.QProgressBar()
        self.progressbar_decrypt.setValue(0)
        self.progressbar_decrypt.setFormat("%p%")
        self.progressbar_decrypt.setTextVisible(False)
        self.progressbar_decrypt.setObjectName("progressbar")
        line1_layout.addWidget(self.progressbar_decrypt)

        btn = QtWidgets.QPushButton("Extract")
        btn.pressed.connect(self.selectInputExtract)
        btn.setFixedSize(150, 40)
        line2_layout.addWidget(btn)
        self.disable_while_extracting.append(btn)

        btn = QtWidgets.QPushButton("Select output folder")
        btn.pressed.connect(self.selectOutputExtract)
        btn.setFixedSize(150, 40)
        line2_layout.addWidget(btn)
        self.disable_while_extracting.append(btn)

        self.btn_extract_go = QtWidgets.QPushButton("GO!")
        self.btn_extract_go.setFixedSize(40, 40)
        self.btn_extract_go.pressed.connect(self.extractGoClick)
        line2_layout.addWidget(self.btn_extract_go)
        self.disable_while_extracting.append(self.btn_extract_go)

        self.progressbar_extract = QtWidgets.QProgressBar()
        self.progressbar_extract.setValue(0)
        self.progressbar_extract.setFormat("%p%")
        self.progressbar_extract.setTextVisible(False)
        self.progressbar_extract.setObjectName("progressbar")
        line2_layout.addWidget(self.progressbar_extract)

        self.checkbox_delete_pack_after = QtWidgets.QCheckBox("Delete data.pack after decryption", self)
        checkbox_layout.addWidget(self.checkbox_delete_pack_after)
        self.disable_while_decrypring.append(self.checkbox_delete_pack_after)

        self.checkbox_delete_decrypted_after = QtWidgets.QCheckBox("Delete decrypted data.pack after extraction", self)
        checkbox_layout.addWidget(self.checkbox_delete_decrypted_after)
        self.disable_while_extracting.append(self.checkbox_delete_decrypted_after)

        self.mainWidget = QtWidgets.QWidget()
        self.mainWidget.setLayout(main_layout)

        self.checkButtons()

    def ui(self):
        return self.mainWidget

    def errorWindow(self, title, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(message)
        msg.resize(400, 300)
        msg.setWindowTitle(title)
        msg.exec_()

    def canDecrypt(self):
        if self.pack_file and self.destination_file:
            return True
        else:
            return False

    def canExtract(self):
        if self.pack_decrypted_pack and self.destination_folder:
            return True
        else:
            return False

    def checkButtons(self):
        if self.is_decrypting:
            for btn in self.disable_while_decrypring:
                btn.setEnabled(False)
        else:
            for btn in self.disable_while_decrypring:
                btn.setEnabled(True)
            if self.canDecrypt() == False:
                self.btn_decrypt_go.setEnabled(False)

        if self.is_extracting:
            for btn in self.disable_while_extracting:
                btn.setEnabled(False)
        else:
            for btn in self.disable_while_extracting:
                btn.setEnabled(True)
            if self.canExtract() == False:
                self.btn_extract_go.setEnabled(False)
           

    def selectInputDecryption(self):
        path = askopenfilename(title="Select the original data.pack", initialfile = 'data.pack', defaultextension=".pack",filetypes=[("Epic Seven Data","*.pack"), ("All Files","*.*")])
        if path != "":
            check = checkValidDataPack(path)
            if check == 1:
                self.pack_file = path
                self.checkButtons()
            else:
                self.errorWindow('Error', 'Not a valid Epic Seven data.pack.')

    def selectOutputDecryption(self):
        path = asksaveasfilename(title="Output file", initialfile = 'data.decrypted', filetypes=[("Epic Seven Pack Decrypted","*.decrypted"), ("All Files","*.*")])
        if path != "":
            self.destination_file = path
            self.checkButtons()

    def selectInputExtract(self):
        path = askopenfilename(title="Select the decrypted data.pack", initialfile = 'data.decrypted', filetypes=[("Epic Seven Pack Decrypted","*.decrypted"), ("All Files","*.*")])
        if path != "":
            check = checkValidDataPack(path)
            if check == 2:
                self.pack_decrypted_pack = path
                self.checkButtons()
            else:
                self.errorWindow('Error', 'Not a valid Epic Seven data.pack.')

    def selectOutputExtract(self):
        path = askdirectory(title="Select where to extract files")
        if path != "":
            self.destination_folder = path
            self.checkButtons()



    ######################################## DECRYPT
    def decryptGoClick(self):
        if self.canDecrypt() == False:
            return

        self.is_decrypting = True
        self.checkButtons()
        self.progressbar_decrypt.setValue(0)

        # Pass the function to execute
        worker = Worker(decrypt, self.pack_file, self.destination_file)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.decryptResult)
        worker.signals.finished.connect(self.decryptComplete)
        worker.signals.progress.connect(self.decryptProgressDisplay)
        worker.signals.error.connect(self.decryptError)
        # Execute
        ThreadPool.start(worker)

    def decryptResult(self, el):
        if self.checkbox_delete_pack_after.isChecked():
            if os.path.exists(self.pack_file):
               os.remove(self.pack_file)
            else:
               self.errorWindow('Error', "Could not delete original data.pack.\n" + self.pack_file + " doesn't exist.")

            self.pack_file = None

    def decryptProgressDisplay(self, val):
        self.progressbar_decrypt.setValue(val)

    def decryptComplete(self):
        self.is_decrypting = False
        self.checkButtons()

    def decryptError(self, err):
        a,b,c = err
        self.errorWindow('Error', str(b))

    ######################################## EXTRACT
    def extractGoClick(self):
        if self.canExtract() == False:
            return

        self.is_extracting = True
        self.checkButtons()
        self.progressbar_extract.setValue(0)

        # Pass the function to execute
        worker = Worker(extract, self.pack_decrypted_pack, self.destination_folder) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.extractResult)
        worker.signals.finished.connect(self.extractComplete)
        worker.signals.progress.connect(self.extractProgressDisplay)
        worker.signals.error.connect(self.decryptError)

        # Execute
        ThreadPool.start(worker)

    def extractResult(self, el): # This will run only if no errors are raised
        if self.checkbox_delete_decrypted_after.isChecked():
            if os.path.exists(self.pack_decrypted_pack):
                os.remove(self.pack_decrypted_pack)
            else:
                self.errorWindow('Error', "Could not delete decrypted data.pack.\n" + self.pack_decrypted_pack + " doesn't exist.")

            self.pack_decrypted_pack = None

    def extractProgressDisplay(self, val):
        self.progressbar_extract.setValue(val)

    def extractComplete(self):
        self.is_extracting = False
        self.checkButtons()

