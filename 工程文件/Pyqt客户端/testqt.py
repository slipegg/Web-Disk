# # -*- coding: utf-8 -*-
#
# from PyQt5 import QtCore, QtWidgets
# from PyQt5.QtWidgets import QProgressBar, QLabel, QApplication, QMainWindow
# from PyQt5.QtCore import QBasicTimer
#
# import sys
#
# class Ui_MainWindow(QMainWindow):
#     def __init__(self,parent=None):
#         super(Ui_MainWindow,self).__init__(parent)
#         self.setupUi()
#         #这里可以定义一些为当前类所用的全局变量
#         self.filepath = ''
#
#
#     def setupUi(self):
#         #设置窗口对象名称
#         self.setObjectName("MainWindow")
#         #设置窗口大小
#         self.resize(800, 600)
#
#         #定义按钮
#         self.startButton = QtWidgets.QPushButton(self)
#         # 设置按钮对象名称（不是按钮显示内容）
#         self.startButton.setObjectName("pred")
#         #设置按钮位置
#         self.startButton.setGeometry(QtCore.QRect(10, 300, 93, 28))
#         #设置按钮显示内容
#         self.startButton.setText("开始")
#         #为按钮绑定事件（点击按钮时就触发）
#         self.startButton.clicked.connect(self.predict)
#
#         #这里我绑定的是具体的业务处理函数，如果你想点击按钮就开始走进度条，则用下面这句
#         # 也可以直接为按钮绑定事件，点击按钮时，就开始走进度条
#         # self.startButton.clicked.connect(self.onStart)
#
#
#
#         #定义状态栏
#         self.statusbar = QtWidgets.QStatusBar(self)
#         # 将状态栏设置为当前窗口的状态栏
#         self.setStatusBar(self.statusbar)
#         # 设置状态栏的对象名称
#         self.statusbar.setObjectName("statusbar")
#         #设置状态栏样式
#         self.statusbar.setStyleSheet('QStatusBar::item {border: none;}')
#
#         # 定义文本标签
#         self.statusLabel = QLabel()
#         # 设置文本标签显示内容
#         self.statusLabel.setText("     准备     ")
#
#
#         #定义水平进度条
#         self.progressBar = QProgressBar()
#         # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
#         self.progressBar.setRange(0, 100)
#         # 设置进度条的初始值
#         self.progressBar.setValue(0)
#
#
#         #设置定时器（走进度条的时候需要使用，否则进度条不会变化，而是固定不变
#         self.timer = QBasicTimer()
#         self.step = 0
#
#
#
#         # 往状态栏中添加组件（stretch应该是拉伸组件宽度）
#         self.statusbar.addPermanentWidget(self.startButton, stretch=0)
#         self.statusbar.addPermanentWidget(self.statusLabel, stretch=2)
#         self.statusbar.addPermanentWidget(self.progressBar, stretch=10)
#
#
#         #其他界面设置
#         self.retranslateUi()
#         QtCore.QMetaObject.connectSlotsByName(self)
#
#
#     def retranslateUi(self):
#         _translate = QtCore.QCoreApplication.translate
#         #设置窗口标题
#         self.setWindowTitle(_translate("MainWindow", "testLoading"))
#
#
#     #   每一个QObject对象或其子对象都有一个QObject.timerEvent方法。
#     #   为了响应定时器的超时事件，需要重写进度条的timerEvent方法。
#     def timerEvent(self, event):
#         if self.step >= 100:
#             self.timer.stop()
#             # 修改文本标签显示内容
#             self.statusLabel.setText("     预测完成    ")
#             # 启用按钮
#             self.startButton.setEnabled(True)
#             # 修改按钮显示内容
#             self.startButton.setText("开始")
#             return
#         #累计步数
#         self.step = self.step + 1
#         #修改进度条的值
#         self.progressBar.setValue(self.step)
#
#
#     def onStart(self):
#         # 修改文本标签显示内容
#         self.statusLabel.setText("     请稍后     ")
#         #禁用按钮
#         self.startButton.setEnabled(False)
#         #修改按钮显示内容
#         self.startButton.setText("预测中...")
#         #使用定时器的start()方法启动定时器，激活进度条。其中：
#         # 参数1：超时时间；参数2：到了超时时间后，接收定时器触发超时事件的对象。
#         self.timer.start(100, self)
#
#
#
#     #处理具体的业务逻辑，如调用深度学习模型进行预测。
#     def predict(self):
#         self.onStart()
#         ################用print模拟模型的调用####################
#         print('predict.......')
#
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ui = Ui_MainWindow()
#     ui.show()
#     sys.exit(app.exec_())
#
#


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys


class NewTableWidget(QWidget):

    def __init__(self):
        super(NewTableWidget, self).__init__()
        self.resize(800, 300)
        self.setWindowTitle('例子')

        # 表头标签
        heaerlabels = ['标题1', '标题2']
        # 行数和列数
        self.rowsnum, self.columnsnum = 2, len(heaerlabels)  # 默认2行2列

        self.TableWidget = QTableWidget(self.rowsnum, self.columnsnum)

        # todo 优化 2 设置水平方向表格为自适应的伸缩模式
        self.TableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.TableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Todo 优化 5 将行与列的高度设置为所显示的内容的宽度高度匹配
        QTableWidget.resizeColumnsToContents(self.TableWidget)
        QTableWidget.resizeRowsToContents(self.TableWidget)

        # 设置水平方向的表头标签与垂直方向上的表头标签，注意必须在初始化行列之后进行，否则，没有效果
        self.TableWidget.setHorizontalHeaderLabels(heaerlabels)
        # Todo 优化1 设置垂直方向的表头标签
        # TableWidget.setVerticalHeaderLabels(['行1', '行2', '行3', '行4'])

        # 添加单元格初始化内容
        for i in range(self.rowsnum):
            for j in range(self.columnsnum - 1):
                newItem = QTableWidgetItem('数据' + str(i) + ',' + str(j))
                newItem.setTextAlignment(Qt.AlignCenter)
                self.TableWidget.setItem(i, j, newItem)

        # 添加单按钮
        self.singlebtn = QPushButton("单按钮")
        self.TableWidget.setCellWidget(0, self.columnsnum - 1, self.singlebtn)
        # 单按钮联动
        self.singlebtn.clicked.connect(self.single_loc)  # 返回按钮位置信息

        # 添加双按钮
        self.doublebtn1 = QPushButton("双按钮1")
        self.doublebtn2 = QPushButton("双按钮2")

        mywidget = QWidget()
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.doublebtn1)
        hlayout.addWidget(self.doublebtn2)
        mywidget.setLayout(hlayout)

        self.TableWidget.setCellWidget(1, self.columnsnum - 1, mywidget)

        # 双按钮联动
        self.doublebtn1.clicked.connect(self.double0_loc)  # 返回按钮位置信息
        self.doublebtn2.clicked.connect(self.double1_loc)  # 返回按钮位置信息

        # self.TableWidget.update()

        # 表格中不显示分割线
        # TableWidget.setShowGrid(False)

        # 隐藏垂直头标签
        # TableWidget.verticalHeader().setVisible(False)

        layout = QHBoxLayout()
        layout.addWidget(self.TableWidget)
        self.setLayout(layout)

        # 返回文本
        self.TableWidget.itemClicked.connect(self.show_data)

    def single_loc(self):
        button = self.sender()
        if button:
            # 确定位置的时候这里是关键
            row = self.TableWidget.indexAt(button.pos()).row()
            column = self.TableWidget.indexAt(button.pos()).column()
            # self.tableWidget.removeRow(row)
            print('单按钮位置: ', row, column)

    def double0_loc(self):
        button = self.sender()
        if button:
            # 确定位置的时候这里是关键
            row = self.TableWidget.indexAt(button.parent().pos()).row()
            column = self.TableWidget.indexAt(button.parent().pos()).column()
            # self.tableWidget.removeRow(row)
            print('双按钮1位置: ', row, column, 0)

    def double1_loc(self):
        button = self.sender()
        if button:
            # 确定位置的时候这里是关键
            row = self.TableWidget.indexAt(button.parent().pos()).row()
            column = self.TableWidget.indexAt(button.parent().pos()).column()
            # self.tableWidget.removeRow(row)
            print('双按钮2位置: ', row, column, 1)

    # 自定义槽函数 show_data()
    # 这里会接收到被点击的单元格对象参数
    def show_data(self, Item=None):
        # 如果单元格对象为空
        if Item is None:
            return
        else:
            row = Item.row()  # 获取行数
            col = Item.column()  # 获取列数 注意是column而不是col哦
            text = Item.text()  # 获取内容

            # 输出测试
            print('row = ', row)
            print('col =', col)
            print('text = ', text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = NewTableWidget()
    win.show()
    sys.exit(app.exec_())

