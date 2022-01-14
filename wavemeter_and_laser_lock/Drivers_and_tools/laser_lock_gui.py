# -*- coding: utf-8 -*-

'''
Created on 

@author: A.Wallucks

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2021, GroeblacherLab
All rights reserved.


The GUI for the laser_lock structure (position of te graphs, boxes, ...)

'''



# Form implementation generated from reading ui file 'laser_lock_gui_3_0.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(305, 175)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.gridLayout_7 = QtWidgets.QGridLayout()
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.comboBox = QtWidgets.QComboBox(Dialog)
        self.comboBox.setMaximumSize(QtCore.QSize(100, 16777215))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.setItemText(0, "")
        self.gridLayout_3.addWidget(self.comboBox, 1, 0, 1, 1)
        self.wl_lineedit = QtWidgets.QLineEdit(Dialog)
        self.wl_lineedit.setMaximumSize(QtCore.QSize(100, 16777215))
        self.wl_lineedit.setObjectName("wl_lineedit")
        self.gridLayout_3.addWidget(self.wl_lineedit, 2, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setMaximumSize(QtCore.QSize(50, 16777215))
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 3, 1, 1, 1)
        self.det_lineedit = QtWidgets.QLineEdit(Dialog)
        self.det_lineedit.setMinimumSize(QtCore.QSize(100, 0))
        self.det_lineedit.setMaximumSize(QtCore.QSize(100, 16777215))
        self.det_lineedit.setObjectName("det_lineedit")
        self.gridLayout_3.addWidget(self.det_lineedit, 3, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout_3.addWidget(self.label, 2, 1, 1, 1)
        self.btn_stop = QtWidgets.QPushButton(Dialog)
        self.btn_stop.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btn_stop.setObjectName("btn_stop")
        self.gridLayout_3.addWidget(self.btn_stop, 3, 2, 1, 1)
        self.horizontalSlider = QtWidgets.QSlider(Dialog)
        self.horizontalSlider.setMaximumSize(QtCore.QSize(100, 16777215))
        self.horizontalSlider.setMinimum(-1000)
        self.horizontalSlider.setMaximum(1000)
        self.horizontalSlider.setPageStep(1)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.gridLayout_3.addWidget(self.horizontalSlider, 4, 0, 1, 1)
        self.spinBox = QtWidgets.QSpinBox(Dialog)
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(20)
        self.spinBox.setObjectName("spinBox")
        self.gridLayout_3.addWidget(self.spinBox, 4, 1, 1, 1)
        self.out_label = QtWidgets.QLabel(Dialog)
        self.out_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.out_label.setObjectName("out_label")
        self.gridLayout_3.addWidget(self.out_label, 4, 2, 1, 1)
        self.btn_start = QtWidgets.QPushButton(Dialog)
        self.btn_start.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btn_start.setObjectName("btn_start")
        self.gridLayout_3.addWidget(self.btn_start, 1, 2, 1, 1)
        self.btn_pause = QtWidgets.QPushButton(Dialog)
        self.btn_pause.setObjectName("btn_pause")
        self.gridLayout_3.addWidget(self.btn_pause, 2, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 0, 1, 1, 1)
        self.update_lineedit = QtWidgets.QLineEdit(Dialog)
        self.update_lineedit.setMaximumSize(QtCore.QSize(100, 16777215))
        self.update_lineedit.setObjectName("update_lineedit")
        self.gridLayout_3.addWidget(self.update_lineedit, 0, 2, 1, 1)
        self.gridLayout_7.addLayout(self.gridLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_3.addLayout(self.gridLayout_7)
        self.plot_placeholder = QtWidgets.QGridLayout()
        self.plot_placeholder.setObjectName("plot_placeholder")
        self.horizontalLayout_3.addLayout(self.plot_placeholder)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Laser Lock"))
        self.wl_lineedit.setText(_translate("Dialog", "1550.0"))
        self.label_3.setText(_translate("Dialog", "Laser"))
        self.label_2.setText(_translate("Dialog", "GHz"))
        self.det_lineedit.setText(_translate("Dialog", "0.0"))
        self.label.setText(_translate("Dialog", "nm"))
        self.btn_stop.setText(_translate("Dialog", "Stop"))
        self.out_label.setText(_translate("Dialog", "Out: 0 V"))
        self.btn_start.setText(_translate("Dialog", "Start"))
        self.btn_pause.setText(_translate("Dialog", "Pause"))
        self.label_4.setText(_translate("Dialog", "update (s)"))
        self.update_lineedit.setText(_translate("Dialog", "0.2"))

