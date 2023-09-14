# Form implementation generated from reading ui file 'Base.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        # Form.resize(550, 84)
        Form.setFixedSize(550, 84)
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setGeometry(QtCore.QRect(30, 30, 500, 35))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progress_info_label = QtWidgets.QLabel(self)
        self.progress_info_label.move( 30, 10 )
        self.progress_info_label.adjustSize()
        self.progressBar.setSizePolicy(sizePolicy)
        self.progressBar.setMinimumSize(QtCore.QSize(500, 35))
        self.progressBar.setMaximumSize(QtCore.QSize(500, 35))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        QtCore.QMetaObject.connectSlotsByName(Form)