# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'download.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(587, 264)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setGeometry(QtCore.QRect(10, 0, 571, 251))
        self.tableWidget.setStyleSheet("/*表格的一种美化方式*/\n"
"\n"
"\n"
"    QHeaderView::section\n"
"{\n"
"    font-size:15px;\n"
"    font-family:\"Microsoft YaHei\";\n"
"    text-align:left;\n"
"    min-height:30px;\n"
"    max-height:49px;\n"
"    margin-left:0px;\n"
"    padding-left:0px;\n"
"    border:1px solid #130c0e ;\n"
"    font:Bold;\n"
"    color:white;\n"
"    background-color:\"#426ab3\";\n"
"\n"
"}/*\n"
"QBrush\n"
"{\n"
"color:red;\n"
"}\n"
"\n"
"QHeaderView::section\n"
"{\n"
"    font-size:20px;\n"
"    font-family:\"Microsoft YaHei\";\n"
"    color:#FFFFFF;\n"
"    text-align:left;\n"
"    min-height:49px;\n"
"    max-height:49px;\n"
"    margin-left:0px;\n"
"    padding-left:0px;\n"
"}*/\n"
"\n"
"/*background:#FFFFFF;\n"
"QTableWidget\n"
"{\n"
"    border:none;\n"
"    font-size:20px;\n"
"    font-family:\"Microsoft YaHei\";\n"
"    color:rgb(25,35,45);\n"
"}\n"
"\n"
"\n"
"QTableWidget::item\n"
"{\n"
"    border-bottom:1px solid #EEF1F7 ;\n"
"    color:rgb(25,35,45);\n"
"}*/\n"
"/*\n"
"QTableWidget::item::selected\n"
"{\n"
"    color:#45b97c;\n"
"}\n"
"*/\n"
"\n"
"QScrollBar::handle:vertical\n"
"{\n"
"    background: rgba(255,255,255,20%);\n"
"    border: 0px solid grey;\n"
"    border-radius:3px;\n"
"    width: 8px;\n"
"}\n"
"\n"
"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical\n"
"{\n"
"    background:rgba(255,255,255,10%);\n"
"}\n"
"\n"
"\n"
"QScollBar::add-line:vertical, QScrollBar::sub-line:vertical\n"
"{\n"
"    background:transparent;\n"
"}\n"
"")
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(70)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "文件名"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "md5码"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "文件长度"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "下载进度"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "操作"))
